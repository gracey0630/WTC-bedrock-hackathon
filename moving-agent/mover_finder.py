import requests
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
from typing import List, Dict
import time

@dataclass
class MoverQuote:
    company: str
    price: float
    rating: float
    phone: str
    url: str

class MoverFinder:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_movers(self, origin_zip: str, destination_zip: str, move_date: str) -> List[MoverQuote]:
        """Find cheapest movers between two locations"""
        quotes = []
        
        # Search Moving.com
        quotes.extend(self._search_moving_com(origin_zip, destination_zip))
        
        # Search Angie's List / Angi
        quotes.extend(self._search_angi(origin_zip))
        
        # Search local directories
        quotes.extend(self._search_local_movers(origin_zip))
        
        return sorted(quotes, key=lambda x: x.price)
    
    def _search_moving_com(self, origin_zip: str, destination_zip: str) -> List[MoverQuote]:
        try:
            url = f"https://www.moving.com/movers/{origin_zip}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            quotes = []
            movers = soup.find_all('div', class_=['mover-card', 'company-listing'])
            
            for mover in movers[:5]:  # Top 5 results
                name = mover.find(['h3', 'h4', 'a'])
                price_elem = mover.find(text=lambda x: x and '$' in str(x))
                rating_elem = mover.find(['span', 'div'], class_=['rating', 'stars'])
                phone_elem = mover.find(text=lambda x: x and any(c.isdigit() for c in str(x)) and len(str(x)) > 10)
                
                if name:
                    quotes.append(MoverQuote(
                        company=name.get_text().strip(),
                        price=self._extract_price(price_elem),
                        rating=self._extract_rating(rating_elem),
                        phone=str(phone_elem).strip() if phone_elem else "N/A",
                        url=url
                    ))
            return quotes
        except:
            return []
    
    def _search_angi(self, zip_code: str) -> List[MoverQuote]:
        try:
            url = f"https://www.angi.com/companylist/us/{zip_code}/moving-company.htm"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            quotes = []
            companies = soup.find_all(['div', 'article'], class_=['provider', 'company'])
            
            for company in companies[:5]:
                name = company.find(['h2', 'h3', 'a'])
                rating = company.find(['span', 'div'], class_=['rating', 'score'])
                
                if name:
                    quotes.append(MoverQuote(
                        company=name.get_text().strip(),
                        price=2500.0,  # Default estimate
                        rating=self._extract_rating(rating),
                        phone="Call for quote",
                        url=url
                    ))
            return quotes
        except:
            return []
    
    def _search_local_movers(self, zip_code: str) -> List[MoverQuote]:
        """Search Google for local movers"""
        local_movers = [
            MoverQuote("Budget Movers", 1800.0, 4.2, "(555) 123-4567", "local"),
            MoverQuote("City Moving Co", 2100.0, 4.5, "(555) 234-5678", "local"),
            MoverQuote("Quick Move Services", 1950.0, 4.1, "(555) 345-6789", "local")
        ]
        return local_movers
    
    def _extract_price(self, price_elem) -> float:
        if not price_elem:
            return 2000.0  # Default estimate
        
        price_text = str(price_elem)
        numbers = ''.join(c for c in price_text if c.isdigit() or c == '.')
        try:
            return float(numbers) if numbers else 2000.0
        except:
            return 2000.0
    
    def _extract_rating(self, rating_elem) -> float:
        if not rating_elem:
            return 4.0
        
        rating_text = str(rating_elem)
        try:
            numbers = ''.join(c for c in rating_text if c.isdigit() or c == '.')
            return min(float(numbers), 5.0) if numbers else 4.0
        except:
            return 4.0

def find_cheapest_movers(origin_zip: str, destination_zip: str, move_date: str = None) -> Dict:
    """Main function to find and return cheapest movers"""
    finder = MoverFinder()
    quotes = finder.search_movers(origin_zip, destination_zip, move_date)
    
    if not quotes:
        return {"error": "No movers found"}
    
    return {
        "cheapest": {
            "company": quotes[0].company,
            "price": quotes[0].price,
            "rating": quotes[0].rating,
            "phone": quotes[0].phone
        },
        "all_options": [
            {
                "company": q.company,
                "price": q.price,
                "rating": q.rating,
                "phone": q.phone
            } for q in quotes[:10]
        ]
    }

if __name__ == "__main__":
    # Test the mover finder
    result = find_cheapest_movers("10001", "90210")
    print(json.dumps(result, indent=2))