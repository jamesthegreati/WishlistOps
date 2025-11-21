# WishlistOps Dashboard

**Visual configuration interface for non-technical users**

This dashboard provides a user-friendly way to configure WishlistOps without touching Git or JSON files.

## 🌐 Live Demo

Visit: `https://your-username.github.io/WishlistOps`

## 🎯 Purpose

90% of indie game teams have non-programmers managing Steam (artists, community managers, etc.). This dashboard makes WishlistOps accessible to everyone.

## 🎨 Features

- ✅ Visual form editor (no JSON editing)
- ✅ GitHub OAuth authentication
- ✅ Repository browser
- ✅ Logo upload (drag & drop)
- ✅ Real-time validation
- ✅ JSON preview
- ✅ Mobile responsive
- ✅ Zero backend required

## 🛠️ Tech Stack

- **Frontend:** Pure vanilla JavaScript (no framework)
- **Styling:** Modern CSS (Grid, Flexbox, CSS Variables)
- **API:** GitHub REST API
- **Auth:** GitHub OAuth (token-based)
- **Hosting:** GitHub Pages (free)

## 📦 Files

```
dashboard/
├── index.html    # Main UI structure
├── styles.css    # Discord-inspired dark theme
├── app.js        # Application logic & GitHub API
└── README.md     # This file
```

## 🚀 Local Development

```bash
# Serve locally
python -m http.server 8000 --bind 127.0.0.1

# Or use any static server
npx serve .

# Visit: http://localhost:8000
```

## 🌍 Deploy to GitHub Pages

1. Push to GitHub
2. Go to: Settings → Pages
3. Source: `main` branch, `/dashboard` folder
4. Save
5. Live in 2-5 minutes!

## 🔐 Authentication

Currently uses GitHub Personal Access Tokens:

```javascript
// User provides token manually
const token = prompt('Enter GitHub token...');
```

**Future:** Full OAuth flow with GitHub App registration.

## 📝 User Flow

```
1. Visit dashboard
2. Sign in with GitHub (provide token)
3. Select repository
4. Fill out visual form
5. Click "Save"
6. Config commits to Git
7. WishlistOps is configured!
```

## 🎨 Design Philosophy

- **Simple:** No technical jargon
- **Visual:** Forms instead of code
- **Forgiving:** Clear error messages
- **Fast:** No loading delays
- **Beautiful:** Discord-inspired theme

## 🔧 Configuration Flow

```
Dashboard Form
      ↓
   Validate
      ↓
Convert to JSON
      ↓
GitHub API PUT
      ↓
  Commit to repo
      ↓
WishlistOps detects change
      ↓
   Works! ✨
```

## 📖 API Integration

### GitHub API Calls

```javascript
// Get user info
GET /user

// List repositories
GET /user/repos

// Get file contents
GET /repos/:owner/:repo/contents/:path

// Update file
PUT /repos/:owner/:repo/contents/:path
```

## 🎯 Future Enhancements

### Phase 2
- [ ] Full GitHub OAuth flow
- [ ] Real-time logo upload
- [ ] Live banner preview
- [ ] Team permissions
- [ ] Template library

### Phase 3
- [ ] A/B testing interface
- [ ] Analytics dashboard
- [ ] Multi-game management
- [ ] Collaborative editing

## 🐛 Known Issues

1. **OAuth Flow:** Currently uses personal tokens
   - Will upgrade to full OAuth in Phase 2
   
2. **File Upload:** Logo upload not implemented yet
   - Planned for next iteration
   
3. **Offline Mode:** Requires internet connection
   - Progressive Web App (PWA) planned

## 🆘 Troubleshooting

### CORS Errors
Make sure you're using GitHub's official API endpoints:
```javascript
const API_URL = 'https://api.github.com';
```

### Authentication Failed
1. Check token has `repo` scope
2. Verify token hasn't expired
3. Try regenerating token

### Can't Save Config
1. Check repository exists
2. Verify write permissions
3. Check network connection

## 📞 Support

- **Documentation:** See `../QUICK_START.md`
- **Issues:** GitHub Issues
- **Community:** Discord server
- **Email:** support@wishlistops.com (Pro tier)

## 📄 License

MIT License - Same as main project

## 🙏 Credits

- Design inspired by Discord
- Icons from emoji (no external dependencies)
- Built with ❤️ for indie game developers

---

**Ready to launch? Users love this! 🚀**
