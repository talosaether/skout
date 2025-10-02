# Authentication Migration Guide

This guide explains how to upgrade your existing Skout installation to use JWT authentication.

## Overview

This migration adds:
- User authentication with JWT tokens
- User ownership of assets (multi-user support)
- Protected API endpoints
- Login/registration UI

## Prerequisites

- Existing Skout installation
- Database backup (recommended)
- Docker and Docker Compose

## Migration Steps

### 1. Backup Your Data

**IMPORTANT:** Always backup your database before running migrations.

```bash
# Backup PostgreSQL database
docker compose exec db pg_dump -U postgres postgres > skout_backup_$(date +%Y%m%d).sql

# Backup file storage (if using volume)
docker run --rm -v skout_server_data:/data -v $(pwd):/backup ubuntu tar czf /backup/server_data_backup_$(date +%Y%m%d).tar.gz /data
```

### 2. Update Environment Variables

Add JWT configuration to your `.env` file:

```bash
# Generate a secure JWT secret (32+ characters)
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"

# Add to .env file
echo "JWT_EXPIRY_HOURS=24" >> .env
```

**Example `.env` file:**
```
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
JWT_SECRET=your-generated-secret-key-here-DO-NOT-SHARE
JWT_EXPIRY_HOURS=24
```

### 3. Stop Running Services

```bash
docker compose down
```

### 4. Pull Latest Code

```bash
git pull origin feature/5-jwt-authentication
# Or merge the PR after approval
```

### 5. Run Database Migration

Apply the authentication schema changes:

```bash
# Start only the database
docker compose up -d db

# Wait for database to be ready
sleep 5

# Apply migration
docker compose exec db psql -U postgres -d postgres -f /docker-entrypoint-initdb.d/migrations/001_add_auth.sql
```

**Alternative:** Manual SQL execution:

```bash
docker compose exec db psql -U postgres -d postgres
```

Then execute:

```sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Add user_id to assets
ALTER TABLE assets ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);
```

### 6. Handle Existing Assets (Choose One Option)

#### Option A: Assign to First User (Recommended)

Existing assets will remain inaccessible until migrated. After creating your first user account:

```sql
-- Get the first user's ID
SELECT id, email FROM users LIMIT 1;

-- Assign all orphaned assets to this user
UPDATE assets SET user_id = '<USER_ID_FROM_ABOVE>' WHERE user_id IS NULL;
```

#### Option B: Create System User

```sql
-- Create system user for orphaned assets
INSERT INTO users (id, email, password_hash)
VALUES (
  '00000000-0000-0000-0000-000000000000',
  'system@skout.internal',
  '$2b$12$dummy.hash.for.system.user.only'
)
ON CONFLICT (id) DO NOTHING;

-- Assign orphaned assets to system user
UPDATE assets SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
```

#### Option C: Delete Orphaned Assets

**WARNING:** This permanently deletes all existing assets!

```sql
-- Delete all assets without user_id
DELETE FROM assets WHERE user_id IS NULL;
```

### 7. Rebuild and Start Services

```bash
# Rebuild with new dependencies
docker compose build

# Start all services
docker compose up -d

# Check logs for errors
docker compose logs -f
```

### 8. Install Frontend Dependencies

```bash
cd client
npm install  # Installs any new dependencies
cd ..
```

### 9. Start Frontend (Development)

```bash
cd client
npm run dev -- --host 0.0.0.0
```

### 10. Register First User

1. Open browser to `https://localhost:5173` (or your dev URL)
2. Click "Register" tab
3. Create your account with:
   - Valid email address
   - Password (min 8 chars, must include uppercase, lowercase, and digit)

### 11. Migrate Existing Assets (If Using Option A)

After registering your first user:

```bash
# Get your user ID from the browser (check localStorage: skout_auth_token)
# Or query the database:
docker compose exec db psql -U postgres -d postgres -c "SELECT id, email FROM users;"

# Assign orphaned assets
docker compose exec db psql -U postgres -d postgres -c "UPDATE assets SET user_id = '<YOUR_USER_ID>' WHERE user_id IS NULL;"
```

## Verification

### 1. Check Database Schema

```bash
docker compose exec db psql -U postgres -d postgres -c "\d users"
docker compose exec db psql -U postgres -d postgres -c "\d assets"
```

Expected output:
- `users` table exists with columns: `id`, `created_at`, `email`, `password_hash`
- `assets` table has new column: `user_id`

### 2. Test Authentication Flow

1. **Registration:**
   - Register a new user
   - Verify you're automatically logged in
   - Check that token is stored in localStorage

2. **Login:**
   - Log out
   - Log back in with same credentials
   - Verify token refresh

3. **Asset Operations:**
   - Upload a new photo
   - View photos (should only see your own)
   - Delete a photo
   - Verify isolation (create second user, confirm cannot see first user's photos)

4. **Token Expiry:**
   - Set `JWT_EXPIRY_HOURS=0.01` (36 seconds) for testing
   - Wait for token to expire
   - Verify automatic logout on next API call

### 3. Check Logs for Errors

```bash
# Backend logs
docker compose logs server

# Frontend terminal output
# Check for any console errors or failed API calls
```

## Rollback Procedure

If migration fails:

### 1. Stop Services

```bash
docker compose down
```

### 2. Restore Database

```bash
# Restore from backup
docker compose up -d db
cat skout_backup_YYYYMMDD.sql | docker compose exec -T db psql -U postgres -d postgres
```

### 3. Restore Code

```bash
git checkout main  # Or your previous branch
```

### 4. Restart Services

```bash
docker compose up -d
cd client && npm run dev
```

## Troubleshooting

### Issue: "JWT_SECRET environment variable must be set"

**Solution:** Ensure `.env` file contains `JWT_SECRET` and restart services:

```bash
docker compose down
docker compose up -d
```

### Issue: Cannot log in after migration

**Possible causes:**
1. JWT_SECRET changed after registration (token invalid)
2. Password requirements not met during registration
3. Email format invalid

**Solution:**
- Clear browser localStorage
- Re-register with valid email and strong password
- Check backend logs for specific error

### Issue: Assets not appearing after migration

**Possible causes:**
1. Assets not assigned to user (user_id IS NULL)
2. Logged in as different user

**Solution:**
```sql
-- Check orphaned assets
SELECT COUNT(*) FROM assets WHERE user_id IS NULL;

-- Check your user ID
SELECT id, email FROM users WHERE email = 'your@email.com';

-- Assign orphaned assets to your user
UPDATE assets SET user_id = '<your-user-id>' WHERE user_id IS NULL;
```

### Issue: "Invalid email format" error

**Solution:** Email must match pattern: `user@domain.tld`

- Must contain `@` symbol
- Must have domain with TLD (.com, .org, etc.)
- Cannot have spaces or special characters (except `.`, `_`, `%`, `+`, `-`)

### Issue: "Password must contain..." error

**Solution:** Password requirements:
- Minimum 8 characters
- At least 1 uppercase letter (A-Z)
- At least 1 lowercase letter (a-z)
- At least 1 digit (0-9)

Example valid passwords:
- `Welcome123`
- `SecurePass1`
- `MyPhoto2025`

### Issue: Frontend build errors after update

**Solution:**
```bash
cd client
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Issue: CORS errors in browser console

**Possible cause:** Frontend and backend URLs mismatch

**Solution:** Verify `vite.config.ts` proxy configuration matches your backend URL.

## Post-Migration Tasks

1. **Update Documentation:** Inform team members of new login requirement
2. **Configure Token Expiry:** Adjust `JWT_EXPIRY_HOURS` based on security needs
3. **Set Up Rate Limiting:** Consider adding Flask-Limiter for login endpoint (future enhancement)
4. **Enable HTTPS:** Ensure production deployment uses HTTPS
5. **Backup Schedule:** Set up automated database backups

## Security Recommendations

1. **JWT Secret:**
   - Use cryptographically random secret (32+ characters)
   - Never commit `.env` to version control
   - Rotate secret periodically (invalidates all tokens)

2. **Password Policy:**
   - Current: 8+ chars, mixed case, digit required
   - Consider: Special character requirement
   - Consider: Password reset flow (not yet implemented)

3. **Token Expiry:**
   - Default: 24 hours
   - Adjust based on security vs. UX trade-off
   - Shorter = more secure, more logins required

4. **HTTPS:**
   - Required for production
   - Camera API requires HTTPS
   - Prevents token interception

5. **Rate Limiting:**
   - Not yet implemented
   - Recommended for `/api/auth/login` endpoint
   - Prevents brute force attacks

## FAQ

**Q: Can I skip the migration and start fresh?**
A: Yes, delete all volumes and rebuild:
```bash
docker compose down -v
docker compose up -d --build
```

**Q: How do I add more users?**
A: Each user must self-register through the UI. No admin panel (yet).

**Q: Can users share assets?**
A: No, assets are private to each user. Sharing is a future enhancement.

**Q: What happens to assets if a user is deleted?**
A: Assets are CASCADE deleted automatically (database constraint).

**Q: Can I change my password?**
A: Not yet implemented. Future enhancement planned.

**Q: How do I revoke a specific token?**
A: Not possible with current stateless JWT implementation. Change JWT_SECRET to invalidate ALL tokens (requires all users to re-login).

## Support

- GitHub Issues: https://github.com/talosaether/skout/issues
- Documentation: See `README.md`, `CLAUDE.md`, and `llms.txt`

## Migration Checklist

- [ ] Backup database
- [ ] Backup file storage
- [ ] Add JWT_SECRET to .env
- [ ] Pull latest code
- [ ] Stop services
- [ ] Run database migration
- [ ] Choose orphaned assets strategy
- [ ] Rebuild services
- [ ] Install frontend dependencies
- [ ] Start services
- [ ] Register first user
- [ ] Migrate existing assets (if applicable)
- [ ] Verify authentication works
- [ ] Test asset upload/download
- [ ] Test multi-user isolation
- [ ] Update team documentation

---

**Migration completed successfully?** Consider submitting feedback on the authentication flow!
