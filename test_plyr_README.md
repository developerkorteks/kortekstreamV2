# Video Player Test Page with Plyr.io

This is a standalone test page for testing the episode detail API endpoint and playing videos using Plyr.io.

## Features

- Modern, minimalist UI using Plyr.io video player
- Support for HTML5, HLS (via hls.js), and iframe video sources
- Responsive design that works on mobile and desktop
- Displays episode details, anime information, and navigation
- Server selection for different video sources
- Episode navigation (previous/next episode)
- Other episodes listing

## How to Use

1. Open the `test_plyr.html` file in your browser
2. Enter an episode URL or slug in the input field (default: "https://gomunime.co/dandadan-season-2-3")
3. Select a category (anime, korean-drama, or all)
4. Check or uncheck "Use full URL" based on what you entered (checked for URLs, unchecked for slugs)
5. Click "Fetch Episode" to load the episode data
6. The video player will automatically load with the first available streaming server
7. You can switch between different streaming servers by clicking the server buttons
8. Use the navigation buttons to go to previous/next episodes or view all episodes

## Technical Details

### Libraries Used

- **Plyr.io (v3.7.8)**: Modern HTML5 video player with a clean UI
- **HLS.js**: For HLS stream support
- **Bootstrap 5**: For responsive layout and styling

### Video Source Support

The player supports three types of video sources:

1. **Regular MP4 Videos**: Standard HTML5 video playback
2. **HLS Streams (.m3u8)**: Using HLS.js for browsers that don't support HLS natively
3. **Iframe Embeds**: For embedded players from external sources

### API Integration

The page integrates with the `/api/v1/episode-detail` endpoint from your API in two ways:

For slugs:
```
GET /api/v1/episode-detail?episode_slug={slug}&category={category}
```

For full URLs:
```
GET /api/v1/episode-detail?id={url}&episode_url={url}&episode_slug={url}&category={category}
```

The page handles different API response structures, including:
- Responses with nested data objects
- Different streaming server formats
- Embed URLs from various providers (Mega, Krakenfiles, etc.)
- Download links that contain streaming URLs

The response is parsed to display:
- Episode title and details
- Anime information (title, thumbnail, genres, synopsis)
- Streaming servers with automatic detection of the appropriate player type
- Navigation links
- Other episodes

## Notes

- This is a standalone test page that doesn't interfere with your Django project
- All functionality is contained within a single HTML file
- No server-side processing is required - it works directly with your API
- The page is designed to be responsive and work on both mobile and desktop devices

## Customization

You can customize the appearance by modifying the CSS in the `<style>` section of the HTML file. The player options can be adjusted in the JavaScript section where Plyr is initialized.