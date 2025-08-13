from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.conf import settings


@cache_page(60 * 60 * 24)  # Cache for 24 hours
@require_http_methods(["GET"])
def robots_txt(request):
    """Generate comprehensive robots.txt file with advanced SEO directives"""
    lines = [
        "# KortekStream - Anime Streaming Platform",
        "# Generated robots.txt for optimal SEO",
        "",
        "User-agent: *",
        "Allow: /",
        "",
        "# High-priority sitemaps",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
        f"Sitemap: {request.build_absolute_uri('/sitemaps/static.xml')}",
        f"Sitemap: {request.build_absolute_uri('/sitemaps/anime.xml')}",
        f"Sitemap: {request.build_absolute_uri('/sitemaps/episodes.xml')}",
        f"Sitemap: {request.build_absolute_uri('/sitemaps/categories.xml')}",
        f"Sitemap: {request.build_absolute_uri('/sitemaps/genres.xml')}",
        "",
        "# Crawl-delay for respectful crawling",
        "Crawl-delay: 1",
        "",
        "# Disallow admin, private, and system areas",
        "Disallow: /admin/",
        "Disallow: /api/private/",
        "Disallow: /api/debug/",
        "Disallow: /api/reset-circuit-breaker/",
        "Disallow: /django-admin/",
        "",
        "# Temporary and cache directories",
        "Disallow: /tmp/",
        "Disallow: /cache/",
        "Disallow: *.tmp$",
        "",
        "# Allow important static resources",
        "Allow: /static/",
        "Allow: /media/",
        "Allow: /favicon.ico",
        "Allow: /robots.txt",
        "Allow: /sitemap.xml",
        "Allow: /.well-known/",
        "",
        "# Google-specific directives",
        "User-agent: Googlebot",
        "Allow: /",
        "Crawl-delay: 1",
        "",
        "# Bing-specific directives", 
        "User-agent: Bingbot",
        "Allow: /",
        "Crawl-delay: 1",
        "",
        "# Baidu-specific (for Asian traffic)",
        "User-agent: Baiduspider",
        "Allow: /",
        "Crawl-delay: 2",
        "",
        "# Social media bots (allow for proper sharing)",
        "User-agent: facebookexternalhit",
        "Allow: /",
        "User-agent: Twitterbot",
        "Allow: /",
        "User-agent: LinkedInBot",
        "Allow: /",
        "",
        "# Block problematic bots",
        "User-agent: SemrushBot",
        "Disallow: /",
        "User-agent: AhrefsBot",
        "Disallow: /",
        "User-agent: MJ12bot",
        "Disallow: /",
        "",
        "# Host directive for proper domain association",
        f"Host: {request.get_host()}",
    ]
    
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@cache_page(60 * 60 * 12)  # Cache for 12 hours
@require_http_methods(["GET"])
def ads_txt(request):
    """Generate ads.txt file for advertising transparency"""
    lines = [
        "# ads.txt file for KortekStream",
        "# This file helps ensure advertising transparency",
        "",
        "# Google AdSense (replace with your actual publisher ID)",
        "google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0",
        "",
        "# Add other advertising partners here",
        "# Format: domain, publisher_id, relationship, certification_authority_id",
    ]
    
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@cache_page(60 * 60 * 24 * 7)  # Cache for 1 week
@require_http_methods(["GET"]) 
def humans_txt(request):
    """Generate humans.txt file for developer credits"""
    lines = [
        "/* TEAM */",
        "Developer: KortekStream Development Team",
        "Contact: admin@kortekstream.com",
        "Location: Indonesia",
        "",
        "/* SITE */",
        "Last update: 2024/01/01",
        "Standards: HTML5, CSS3, JavaScript ES6+",
        "Components: Django, TailwindCSS, Alpine.js",
        "Software: Visual Studio Code, Git",
        "",
        "/* THANKS */",
        "Special thanks to the anime community and all contributors",
        "who make KortekStream possible.",
        "",
        f"Built with ❤️ for anime lovers | {request.get_host()}",
    ]
    
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@cache_page(60 * 5)  # Cache for 5 minutes (frequent updates)
@require_http_methods(["GET"])
def opensearch_xml(request):
    """Generate OpenSearch description for browser search integration"""
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/"
                       xmlns:moz="http://www.mozilla.org/2006/browser/search/">
    <ShortName>KortekStream</ShortName>
    <Description>Search anime on KortekStream - Streaming Anime Terbaik Indonesia</Description>
    <InputEncoding>UTF-8</InputEncoding>
    <Image width="16" height="16" type="image/x-icon">{request.scheme}://{request.get_host()}/static/images/favicon.ico</Image>
    <Image width="32" height="32" type="image/png">{request.scheme}://{request.get_host()}/static/images/favicon-32x32.png</Image>
    <Url type="text/html" template="{request.scheme}://{request.get_host()}/search/?q={{searchTerms}}"/>
    <Url type="application/x-suggestions+json" template="{request.scheme}://{request.get_host()}/api/search/suggestions/?q={{searchTerms}}"/>
    <moz:SearchForm>{request.scheme}://{request.get_host()}/search/</moz:SearchForm>
    <Developer>KortekStream Team</Developer>
    <Contact>admin@kortekstream.com</Contact>
    <Tags>anime streaming indonesia subtitle</Tags>
    <LongName>KortekStream - Platform Streaming Anime Subtitle Indonesia</LongName>
    <Attribution>KortekStream ©2024</Attribution>
    <SyndicationRight>open</SyndicationRight>
    <AdultContent>false</AdultContent>
    <Language>id-ID</Language>
    <Language>en-US</Language>
    <Language>ja-JP</Language>
</OpenSearchDescription>'''
    
    return HttpResponse(xml_content, content_type='application/opensearchdescription+xml')


@cache_page(60 * 60 * 24)  # Cache for 24 hours
@require_http_methods(["GET"])
def manifest_json(request):
    """Generate web app manifest"""
    manifest = {
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
    }
    
    return HttpResponse(
        render_to_string('manifest.json', {'manifest': manifest}),
        content_type='application/json'
    )


@cache_page(60 * 60)  # Cache for 1 hour
@require_http_methods(["GET"])
def security_txt(request):
    """Generate security.txt file for responsible disclosure"""
    lines = [
        "Contact: mailto:security@kortekstream.com",
        "Expires: 2025-12-31T23:59:59.000Z",
        "Preferred-Languages: id, en",
        "Canonical: https://kortekstream.com/.well-known/security.txt",
        "",
        "# Please report security vulnerabilities responsibly",
        "# We appreciate your help in keeping our platform secure",
    ]
    
    return HttpResponse('\n'.join(lines), content_type='text/plain')