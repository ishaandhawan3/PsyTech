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
- **Session-based JSON Storage** - Simple, portable data storage system
- **Beautiful UI** - Custom CSS styling with modern design

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd psyTech
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run frontend/main_app.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://localhost:8501
   ```

## Project Structure

```
psyTech/
├── frontend/
│   ├── main_app.py                 # Main application entry point
│   ├── utils/
│   │   ├── navigation.py           # Navigation utilities
│   │   ├── styling.py              # CSS styling and UI components
│   │   └── json_database_adapter.py # JSON database operations
│   └── service/
│       ├── questionnaire.py        # Multi-step profile form
│       ├── activity_recommendations.py  # Activity cards and recommendations
│       ├── feedback_collection.py  # Feedback forms and collection
│       ├── evaluation_dashboard.py # Progress analytics and charts
│       └── article_feed.py         # Learning resources and articles
├── backend/
│   ├── storage/
│   │   └── json_storage.py         # Core JSON storage functionality
│   └── connectors/
│       └── s3_connection.py        # Optional S3 connectivity
├── data/
│   ├── activities.csv              # Activity database
│   └── sessions/                   # JSON session data (auto-created)
├── test_json_storage.py            # Test script for JSON storage
└── README.md                       # This file
```

## Storage System

The application uses a simple, session-based JSON storage system:

### Key Features
- **Session-based** - Data is organized by user sessions
- **JSON Files** - All data stored in human-readable JSON format
- **Portable** - Easy to backup, transfer, or analyze data
- **No Database Required** - No need for SQL or other database systems
- **Extensible** - Can be extended to support cloud storage (S3)

### Data Types
Each session directory contains separate JSON files for different data types:
- `userprofile.json` - User profile and child information
- `activities.json` - Activity completion records
- `progress.json` - Skills progress tracking
- `feedback.json` - Detailed feedback data
- `feed.json` - Article feed and resources

### Testing the Storage System
Run the included test script to verify the JSON storage system:
```bash
python psyTech/test_json_storage.py
```

This will:
1. Create a test session
2. Save sample user profile, activity, and feedback data
3. Retrieve and display the saved data
4. Show the JSON file structure

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

## Customization

### Adding New Activities
1. Edit `data/activities.csv` with new activity data
2. Include columns: Activity Name, Focus Area(s), Conditions, Other Keywords
3. The system will automatically incorporate new activities

### Styling Modifications
- Edit `frontend/utils/styling.py` to modify CSS styles
- Update color schemes, fonts, and layout
- All styling is centralized for easy customization

### Adding New Features
- Create new page modules in the `frontend/service/` directory
- Update navigation in `frontend/utils/navigation.py`
- Add database operations in `frontend/utils/json_database_adapter.py`

## Technical Details

### Dependencies
- **Streamlit** - Web application framework
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive charts and visualizations
- **JSON** - Data storage format

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

2. **Storage Errors**
   - Check write permissions in the `data/sessions/` directory
   - Ensure JSON files are not manually edited with invalid format

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
