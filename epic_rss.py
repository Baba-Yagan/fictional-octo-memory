#!/usr/bin/env python3
"""
Epic Games Free Games RSS Feed Generator
Fetches free games from Epic Games API and generates an RSS feed
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

API_URL = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
RSS_TITLE = "Epic Games Free Games"
RSS_DESCRIPTION = "Current and upcoming free games from Epic Games Store"
RSS_LINK = "https://epicgames.com/store/free-games"


def fetch_free_games():
    """Fetch free games data from Epic Games API"""
    try:
        req = Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except URLError as e:
        print(f"Error fetching data: {e}")
        return None


def get_game_url(element):
    """Extract game URL from element data"""
    # Try to get pageSlug from catalogNs.mappings or offerMappings
    mappings = element.get('catalogNs', {}).get('mappings', [])
    if not mappings:
        mappings = element.get('offerMappings', [])

    if mappings and mappings[0].get('pageSlug'):
        return f"https://epicgames.com/store/p/{mappings[0]['pageSlug']}"

    # Fallback to productSlug
    if element.get('productSlug'):
        return f"https://epicgames.com/store/p/{element['productSlug']}"

    return "https://epicgames.com/store/free-games"


def parse_games(data):
    """Parse the API response and extract free games"""
    games = []

    if not data or 'data' not in data:
        return games

    elements = data['data']['Catalog']['searchStore'].get('elements', [])

    for element in elements:
        # Check if game is free (price is 0 or has 100% discount)
        price_info = element.get('price', {}).get('totalPrice', {})
        discount_price = price_info.get('discountPrice', 0)

        # Check promotions for 100% discount
        promotions = element.get('promotions') or {}
        is_free = discount_price == 0

        # Check current promotional offers
        current_promos = promotions.get('promotionalOffers', [])
        for promo_group in current_promos:
            for promo in promo_group.get('promotionalOffers', []):
                if promo.get('discountSetting', {}).get('discountPercentage') == 100:
                    is_free = True

        if is_free:
            game_title = element.get('title', 'Unknown Game')
            game_url = get_game_url(element)
            description = element.get('description', '')

            # Get promotion dates
            pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            for promo_group in current_promos:
                for promo in promo_group.get('promotionalOffers', []):
                    if promo.get('discountSetting', {}).get('discountPercentage') == 100:
                        try:
                            start_date = datetime.fromisoformat(promo['startDate'].replace('Z', '+00:00'))
                            pub_date = start_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                        except:
                            pass

            games.append({
                'title': game_title,
                'link': game_url,
                'description': description,
                'pub_date': pub_date
            })

        # Check upcoming free games
        upcoming_promos = promotions.get('upcomingPromotionalOffers', [])
        for promo_group in upcoming_promos:
            for promo in promo_group.get('promotionalOffers', []):
                if promo.get('discountSetting', {}).get('discountPercentage') == 100:
                    game_title = element.get('title', 'Unknown Game')
                    game_url = get_game_url(element)
                    description = element.get('description', '')

                    # Get start date for upcoming
                    pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                    try:
                        start_date = datetime.fromisoformat(promo['startDate'].replace('Z', '+00:00'))
                        pub_date = start_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                    except:
                        pass

                    games.append({
                        'title': f"[UPCOMING] {game_title}",
                        'link': game_url,
                        'description': description,
                        'pub_date': pub_date
                    })

    return games


def generate_rss(games):
    """Generate RSS feed XML from games list"""
    from xml.dom import minidom

    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')

    # Add channel metadata
    ET.SubElement(channel, 'title').text = RSS_TITLE
    ET.SubElement(channel, 'link').text = RSS_LINK
    ET.SubElement(channel, 'description').text = RSS_DESCRIPTION
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

    # Add items
    for game in games:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = game['title']
        ET.SubElement(item, 'link').text = game['link']
        ET.SubElement(item, 'description').text = game['description']
        ET.SubElement(item, 'pubDate').text = game['pub_date']

    # Pretty print
    xml_str = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ')


def main():
    """Main function"""
    print("Fetching free games from Epic Games...")
    data = fetch_free_games()

    if not data:
        print("Failed to fetch data from API")
        return

    games = parse_games(data)

    if not games:
        print("No free games found")
        return

    print(f"Found {len(games)} free game(s)")
    rss_feed = generate_rss(games)

    # Output to file
    with open('epic_free_games.rss', 'w', encoding='utf-8') as f:
        f.write(rss_feed)

    print("RSS feed generated: epic_free_games.rss")


if __name__ == '__main__':
    main()
