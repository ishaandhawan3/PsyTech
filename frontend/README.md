# PsyTech Child Wellness Companion

A comprehensive multi-page Streamlit application for child development and wellness tracking.

## Features

### 🔄 Multi-Page Flow
1. **📝 Child Profile Questionnaire** - Comprehensive 5-step form to collect child information
2. **🎯 Activity Recommendations** - Personalized activity cards with interactive feedback
3. **💭 Activity Feedback** - Detailed feedback collection after activity completion
4. **📊 Progress Dashboard** - Analytics, achievements, and progress tracking
5. **📚 Learning Resources** - Personalized article feed and educational content

### ✨ Key Features
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Interactive Activity Cards** - Try, save, skip, and rate activities
- **Progress Tracking** - Skills development radar charts and analytics
- **Achievement System** - Badges and milestones to celebrate progress
- **Personalized Content** - AI-driven recommendations based on child profile
- **Data Persistence** - SQLite database for storing user data
- **Beautiful UI** - Custom CSS styling with modern design

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd psyTech/frontend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run main_app.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://localhost:8501
   ```

## Project Structure

```
psyTech/frontend/
├── main_app.py                 # Main application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── data/
│   ├── activities.csv          # Activity database
│   └── psytech.db             # SQLite database (auto-created)
├── utils/
│   ├── navigation.py          # Navigation utilities
│   ├── styling.py             # CSS styling and UI components
│   └── database.py            # Database operations
└── pages/
    ├── questionnaire.py       # Multi-step profile form
    ├── activity_recommendations.py  # Activity cards and recommendations
    ├── feedback_collection.py # Feedback forms and collection
    ├── evaluation_dashboard.py # Progress analytics and charts
    └── article_feed.py        # Learning resources and articles
```

## Usage Guide

### 1. Complete Child Profile
- Fill out the 5-step questionnaire with your child's information
- Include strengths, challenges, goals, and preferences
- This data drives all personalized recommendations

### 2. Explore Activity Recommendations
- View personalized activity cards based on your child's profile
- Use filters to find activities by duration, difficulty, or skill area
- Try activities, save for later, or skip with feedback

### 3. Provide Activity Feedback
- Give detailed feedback after completing activities
- Rate engagement, difficulty, and effectiveness
- Track time spent and behavioral observations

### 4. Monitor Progress
- View comprehensive dashboard with progress metrics
- See skills development radar chart
- Celebrate achievements and milestones
- Set new goals and track improvement

### 5. Access Learning Resources
- Browse personalized article recommendations
- Search by category or specific topics
- Bookmark helpful articles for later reference

## Database Schema

The application uses SQLite with the following main tables:
- `users` - User profiles and child information
- `activities_completed` - Activity completion records
- `user_progress` - Skills progress tracking
- `activity_feedback` - Detailed feedback data
- `bookmarked_articles` - Saved articles and resources

## Customization

### Adding New Activities
1. Edit `data/activities.csv` with new activity data
2. Include columns: Activity Name, Focus Area(s), Conditions, Other Keywords
3. The system will automatically incorporate new activities

### Styling Modifications
- Edit `utils/styling.py` to modify CSS styles
- Update color schemes, fonts, and layout
- All styling is centralized for easy customization

### Adding New Features
- Create new page modules in the `pages/` directory
- Update navigation in `utils/navigation.py`
- Add database operations in `utils/database.py`

## Technical Details

### Dependencies
- **Streamlit** - Web application framework
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive charts and visualizations
- **SQLite3** - Local database storage

### Key Design Patterns
- **Modular Architecture** - Separate pages and utilities
- **Session State Management** - Persistent user data across pages
- **Progressive Enhancement** - Features unlock as user progresses
- **Responsive Design** - Mobile-first approach

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path includes the project directory

2. **Database Errors**
   - Database is auto-created on first run
   - Check write permissions in the `data/` directory

3. **CSV Loading Issues**
   - Ensure `activities.csv` exists in the `data/` directory
   - Check file encoding (UTF-8 recommended)

4. **Styling Issues**
   - Clear browser cache and refresh
   - Check console for CSS errors

### Performance Tips
- The app caches data loading for better performance
- Large datasets may require optimization
- Consider pagination for extensive activity lists

## Future Enhancements

### Planned Features
- **Multi-child Support** - Manage multiple children in one account
- **Export Functionality** - PDF reports for therapists/teachers
- **Calendar Integration** - Schedule activities and reminders
- **Community Features** - Share experiences with other parents
- **Professional Dashboard** - Tools for therapists and educators

### Integration Opportunities
- **External APIs** - Connect to therapy management systems
- **Wearable Devices** - Track physical activity and engagement
- **Educational Platforms** - Sync with school systems
- **Telehealth** - Integration with virtual therapy sessions

## Support

For questions, issues, or feature requests:
1. Check the troubleshooting section above
2. Review the code documentation in each module
3. Test with sample data to isolate issues

## License

This project is part of the PsyTech Child Wellness Companion system.
