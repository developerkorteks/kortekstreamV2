from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Generate SEO files like robots.txt, sitemap.xml, and other SEO assets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=settings.STATIC_ROOT,
            help='Directory to output SEO files'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        
        if not output_dir:
            output_dir = os.path.join(settings.BASE_DIR, 'static')
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        self.stdout.write(self.style.SUCCESS(f'Generating SEO files in: {output_dir}'))
        
        # Generate robots.txt
        self.generate_robots_txt(output_dir)
        
        # Generate manifest.json
        self.generate_manifest_json(output_dir)
        
        # Generate security.txt
        self.generate_security_txt(output_dir)
        
        # Generate favicon files info
        self.check_favicon_files(output_dir)
        
        self.stdout.write(self.style.SUCCESS('SEO files generated successfully!'))

    def generate_robots_txt(self, output_dir):
        """Generate robots.txt file"""
        robots_content = """User-agent: *
Allow: /

# Sitemaps
Sitemap: https://kortekstream.com/sitemap.xml

# Crawl-delay for respectful crawling
Crawl-delay: 1

# Disallow admin and private areas
Disallow: /admin/
Disallow: /api/private/

# Allow important pages
Allow: /static/
Allow: /media/
"""
        
        robots_path = os.path.join(output_dir, 'robots.txt')
        with open(robots_path, 'w') as f:
            f.write(robots_content)
        
        self.stdout.write(f'Generated: {robots_path}')

    def generate_manifest_json(self, output_dir):
        """Generate web app manifest"""
        manifest_content = """{
    "name": "KortekStream - Streaming Anime Indonesia",
    "short_name": "KortekStream",
    "description": "Platform streaming anime terbaik di Indonesia",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#F59E0B",
    "icons": [
        {
            "src": "/static/images/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/images/icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ],
    "categories": ["entertainment", "video"],
    "lang": "id",
    "orientation": "portrait-primary"
}"""
        
        manifest_path = os.path.join(output_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            f.write(manifest_content)
        
        self.stdout.write(f'Generated: {manifest_path}')

    def generate_security_txt(self, output_dir):
        """Generate security.txt file"""
        security_content = """Contact: mailto:security@kortekstream.com
Expires: 2025-12-31T23:59:59.000Z
Preferred-Languages: id, en
Canonical: https://kortekstream.com/.well-known/security.txt

# Please report security vulnerabilities responsibly
# We appreciate your help in keeping our platform secure
"""
        
        # Create .well-known directory
        well_known_dir = os.path.join(output_dir, '.well-known')
        os.makedirs(well_known_dir, exist_ok=True)
        
        security_path = os.path.join(well_known_dir, 'security.txt')
        with open(security_path, 'w') as f:
            f.write(security_content)
        
        self.stdout.write(f'Generated: {security_path}')

    def check_favicon_files(self, output_dir):
        """Check and create placeholder favicon files if they don't exist"""
        favicon_files = [
            'favicon.ico',
            'images/apple-touch-icon.png',
            'images/favicon-32x32.png',
            'images/favicon-16x16.png',
            'images/icon-192x192.png',
            'images/icon-512x512.png',
            'images/og-image.jpg',
            'images/twitter-image.jpg',
            'images/logo.png'
        ]
        
        for favicon_file in favicon_files:
            file_path = os.path.join(output_dir, favicon_file)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f'Missing: {file_path} - Please add this file for better SEO')
                )
            else:
                self.stdout.write(f'Found: {file_path}')