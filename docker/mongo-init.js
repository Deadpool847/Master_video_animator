// MongoDB initialization script for Video Art Masterpiece
db = db.getSiblingDB('video_art_masterpiece');

// Create admin user for the application database
db.createUser({
  user: 'app_user',
  pwd: 'app_password123',
  roles: [
    {
      role: 'readWrite',
      db: 'video_art_masterpiece'
    }
  ]
});

// Create collections with indexes for better performance
db.createCollection('video_projects');
db.video_projects.createIndex({ "id": 1 }, { unique: true });
db.video_projects.createIndex({ "created_at": -1 });
db.video_projects.createIndex({ "status": 1 });
db.video_projects.createIndex({ "art_style": 1 });

// Insert welcome message
db.system_info.insertOne({
  message: "Video Art Masterpiece Database Initialized Successfully! 🎨",
  created_at: new Date(),
  version: "1.0.0"
});

print("🎨 Video Art Masterpiece database initialized successfully!");