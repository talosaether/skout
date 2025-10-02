# Skout - Project Memory for Claude Code

Last Updated: 2025-10-02

## Project Overview

Skout is an MVP Progressive Web Application for camera-based image capture and management. Built with React/Vite frontend and Flask/PostgreSQL backend, focusing on mobile-first camera functionality.

## Core Architectural Decisions

### 1. Direct SQL Over ORM
**Decision**: Use psycopg with raw SQL instead of SQLAlchemy or other ORMs
**Rationale**: "Killer MVP stack that doesn't bury you in ceremony" - full control, better performance for simple CRUD
**Implementation**: All database operations in `server/app.py` and `server/db.py` use parameterized queries
**Never**: Use string concatenation for SQL - always parameterize to prevent SQL injection

### 2. Hash-Based File Storage (Migration from Database Blobs)
**Original Design**: Store image binary data in PostgreSQL `bytea` column
**Current Design**: Hash-based file storage on filesystem
**Migration Date**: September 19, 2025 (commit 115dffe)
**Rationale**:
- Better performance for binary asset retrieval
- Easier scaling (filesystem vs database growth)
- Reduced database bloat
- Content-addressable storage enables deduplication

**Implementation Details**:
- Images stored in `/server/data` directory (persisted via Docker volume)
- Metadata (id, filename, mime, size, timestamps) remains in PostgreSQL
- Hash-based naming prevents filename conflicts

### 3. Mobile-First PWA Architecture
**Camera Requirements**:
- MUST use HTTPS for camera access (browser security requirement)
- `playsInline` attribute required for iOS Safari
- `facingMode: { ideal: "environment" }` prefers rear camera

**Development Workflow**:
```bash
npm run dev -- --host 0.0.0.0  # Expose for mobile device testing
# Use ngrok for HTTPS: ngrok http 5173
```

## Recent Issues & Solutions

### Issue: Missing Take Photo Button (Sept 20, 2025)
**Symptom**: Button not visible in UI
**Root Cause**: CSS framework conflicts
**Solution**: Added inline styles to `CameraCapture.tsx`
**Learning**: Inline styles override framework CSS when conflicts occur
**File**: `client/src/components/CameraCapture.tsx:197-202`

### Issue: Delete Button Modal Functionality (Sept 20, 2025)
**Symptom**: Delete confirmation modal not working
**Root Cause**: Event handling conflicts with framework styles
**Solution**: Fixed with inline styles for proper rendering
**Learning**: Modal components need style isolation
**Commit**: 3aa3300

### Issue: CRUD Integration Failures (Sept 20, 2025)
**Symptom**: End-to-end operations failing
**Root Cause**: Multiple integration points not tested together
**Solution**: Added comprehensive E2E test, fixed all CRUD issues
**Learning**: Integration tests catch issues unit tests miss
**Commit**: 0b128f9
**Recommendation**: Run E2E tests after any API or schema changes

## System Relationships

### Data Flow
```
User → Camera API (getUserMedia) → React Component →
FormData Upload → Flask API → File System + PostgreSQL →
Response → UI Refresh
```

### Key Integration Points
1. **Frontend ↔ Backend**: REST API at `/api/*` endpoints
2. **Backend ↔ Database**: Direct SQL via psycopg connection pool
3. **Backend ↔ File System**: Hash-based storage in `/server/data`
4. **Client ↔ Camera**: Browser getUserMedia API (HTTPS required)

### Docker Services
- `db`: PostgreSQL 16 with persistent volume
- `server`: Flask API with file storage volume mount
- `client`: Vite dev server (development only)

## Code Patterns & Conventions

### Inline Styles for Framework Conflicts
**When**: CSS framework conflicts prevent proper rendering
**Why**: Guarantees style application regardless of cascading
**Where**: Camera button, modal components
**Example**:
```tsx
style={{ display: 'block', width: '100%' }}
```

### Transaction Management
**Pattern**: Context manager for automatic commit/rollback
**Implementation**: `db.py:tx()` context manager
**Usage**:
```python
with tx() as cur:
    cur.execute("INSERT ...", params)
    # Auto-commits on success, auto-rolls back on exception
```

### Error Handling
- Frontend: Try/catch with user-friendly error messages
- Backend: Appropriate HTTP status codes (400, 404, 413, 415, 500)
- File size limit: 7MB (`MAX_BYTES`)
- MIME type validation: Only `image/*` accepted

## File Locations

### Critical Files
- `/server/app.py` - Flask API with all endpoints
- `/server/db.py` - Database connection and transaction helpers
- `/server/schema.sql` - PostgreSQL schema definition
- `/client/src/components/CameraCapture.tsx` - Camera interface
- `/client/src/lib/api.ts` - API client functions
- `/docker-compose.yml` - Service orchestration
- `/server/data/` - Uploaded image storage (volume-mounted)

### Configuration
- `.env` - Environment variables (not committed)
- `.env.example` - Template for environment setup
- `client/vite.config.ts` - Frontend build config with PWA plugin
- `client/tailwind.config.js` - Tailwind CSS configuration

## Development Workflows

### Starting the Application
```bash
# Backend (in project root)
docker compose up -d --build

# Frontend (in client/)
cd client
npm run dev -- --host 0.0.0.0
```

### Mobile Testing
1. Ensure dev server runs with `--host 0.0.0.0`
2. Use ngrok for HTTPS: `ngrok http 5173`
3. Access via HTTPS URL on mobile device
4. Grant camera permissions when prompted

### Database Access
```bash
# Direct PostgreSQL access
docker compose exec db psql -U postgres -d postgres

# View logs
docker compose logs db
docker compose logs server

# Reset database (deletes all data)
docker compose down -v
docker compose up -d
```

### Debugging Common Issues

**Camera Not Working**:
1. Check HTTPS is being used
2. Verify browser permissions granted
3. Check console for getUserMedia errors
4. Ensure `playsInline` attribute exists (iOS)

**Backend Connection Issues**:
1. Verify services running: `docker compose ps`
2. Check logs: `docker compose logs server`
3. Verify ports 8000 and 5432 available
4. Check DATABASE_URL environment variable

**Images Not Persisting**:
1. Verify volume mounts in `docker-compose.yml`
2. Check `/server/data` directory exists in container
3. Review file permissions
4. Check disk space

**Delete Modal Not Working**:
- Check inline styles applied correctly
- Verify event handlers not blocked by CSS

## Future Enhancements (From PRD)

### Next 10% Polish
- JWT authentication (browser Authorization header + pyjwt)
- ETag/Cache-Control for asset endpoints
- PWA background sync for offline uploads
- Rate limiting (Flask-Limiter)
- Migration tooling (current: manual `schema.sql` execution)

### Scaling Considerations
- Move to S3/GCS if file storage outgrows local filesystem
- Add CDN for asset delivery
- Implement image optimization/resizing
- Add thumbnail generation

## Known Limitations

1. **File Size**: 7MB limit per upload
2. **Authentication**: None (MVP only - add before production)
3. **Rate Limiting**: None (add before production)
4. **Image Processing**: No resizing/optimization
5. **Offline Support**: Basic PWA, no background sync yet
6. **CORS**: Open in development (tighten for production)

## Testing Strategy

### End-to-End Testing
**Approach**: Comprehensive CRUD cycle testing
**When**: After any API or database changes
**Coverage**: Create → Read → Update → Delete flows
**Location**: Test files (added Sept 20, 2025)

### Manual Testing Checklist
- [ ] Camera capture on mobile (HTTPS)
- [ ] Image upload and storage
- [ ] Gallery display and pagination
- [ ] Delete with confirmation
- [ ] Data persistence after container restart
- [ ] PWA installation on mobile

## Git Workflow

### Commit Message Style
- Clear, descriptive messages
- Reference specific features/fixes
- Include context when architectural changes made

### Recent Commits (Sept 19-20, 2025)
- Storage migration from bytea to file system
- UI fixes with inline styles
- E2E integration testing
- Persistent volume configuration
- .gitignore cleanup

## Environment Variables

```env
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
FLASK_DEBUG=1  # Development only
```

## Performance Considerations

- Index on `assets.created_at` for pagination efficiency
- Connection pooling via psycopg
- File system storage faster than database blobs
- Vite HMR for fast frontend iteration

---

**Notes for Future Sessions**:
- Always check this file for architectural context
- Update when making significant changes
- Document workarounds and their rationale
- Keep debugging workflows current
