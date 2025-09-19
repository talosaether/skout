# Skout - MVP CRUD Camera PWA

A modern Progressive Web Application for capturing, storing, and managing images with a camera-first interface.

## 🚀 Features

- **📸 Camera Capture**: Real-time camera access with environment-facing camera preference
- **☁️ Cloud Storage**: Upload and store images in PostgreSQL database
- **🖼️ Image Gallery**: Responsive grid layout for viewing uploaded images
- **🗑️ Asset Management**: Delete images with confirmation
- **📱 PWA Ready**: Installable on mobile devices with offline capabilities
- **🎨 Modern UI**: Dark theme with Tailwind CSS styling
- **⚡ Fast Performance**: Vite-powered frontend with hot reload

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling and development
- **Tailwind CSS** for styling
- **PWA Plugin** for service worker and manifest
- **getUserMedia API** for camera access

### Backend
- **Flask** web framework
- **PostgreSQL** database with direct SQL queries
- **psycopg** for database connectivity
- **Flask-CORS** for cross-origin requests

### Infrastructure
- **Docker Compose** for local development
- **Docker** containerization
- **Environment variables** for configuration

## 🏃‍♂️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)

### 1. Clone the Repository
```bash
git clone https://github.com/talosaether/skout.git
cd skout
```

### 2. Start the Backend Services
```bash
# Copy environment variables
cp .env.example .env

# Start PostgreSQL database and Flask API
docker compose up -d --build
```

### 3. Start the Frontend Development Server
```bash
cd client
npm install
npm run dev
```

### 4. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## 📱 Mobile Usage

For camera access on mobile devices:
1. Serve the application over HTTPS (required for camera access)
2. Use tools like `ngrok` for local testing: `ngrok http 5173`
3. Access the application through the HTTPS URL provided

## 🗂️ Project Structure

```
skout/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   └── CameraCapture.tsx
│   │   ├── lib/           # API client and utilities
│   │   │   └── api.ts
│   │   ├── App.tsx        # Main application component
│   │   └── main.tsx       # Application entry point
│   ├── public/            # Static assets and PWA icons
│   ├── vite.config.ts     # Vite configuration with PWA
│   └── package.json       # Frontend dependencies
├── server/                # Flask backend
│   ├── app.py            # Main Flask application
│   ├── db.py             # Database connection and utilities
│   ├── schema.sql        # PostgreSQL schema
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Backend container configuration
├── docker-compose.yml    # Multi-service orchestration
└── .env.example         # Environment variables template
```

## 🔌 API Endpoints

### Health Check
- `GET /api/health` - Service health status

### Assets Management
- `GET /api/assets` - List all assets with pagination
- `POST /api/assets` - Upload new image asset
- `GET /api/assets/{id}` - Retrieve specific asset
- `DELETE /api/assets/{id}` - Delete specific asset

### Request Examples

```bash
# Upload an image
curl -X POST -F "file=@image.jpg" http://localhost:8000/api/assets

# List assets
curl http://localhost:8000/api/assets

# Delete an asset
curl -X DELETE http://localhost:8000/api/assets/{asset-id}
```

## 🔧 Configuration

### Environment Variables

```env
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
```

### File Upload Limits
- Maximum file size: 7MB
- Supported formats: image/* (JPEG, PNG, GIF, WebP, etc.)

## 🚀 Deployment

### Production Deployment

1. **Build the frontend**:
```bash
cd client
npm run build
```

2. **Configure environment variables** for production

3. **Deploy using Docker**:
```bash
docker compose -f docker-compose.prod.yml up -d
```

### PWA Installation
Users can install the app on their devices:
- **Desktop**: Click the install button in the browser address bar
- **Mobile**: Use "Add to Home Screen" option in the browser menu

## 🧪 Development

### Running Tests
```bash
# Backend API testing
curl http://localhost:8000/api/health

# Frontend development
cd client
npm run dev
```

### Database Management
```bash
# Access PostgreSQL directly
docker compose exec db psql -U postgres -d postgres

# View database logs
docker compose logs db

# Reset database
docker compose down -v
docker compose up -d
```

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Troubleshooting

### Camera Not Working
- Ensure HTTPS is used (required for camera access)
- Check browser permissions for camera access
- Verify camera is not being used by another application

### Backend Connection Issues
- Verify Docker services are running: `docker compose ps`
- Check backend logs: `docker compose logs server`
- Ensure ports 8000 and 5432 are available

### Frontend Build Issues
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility (18+)
- Verify all dependencies are installed

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation

---

Built with ❤️ using modern web technologies and best practices.