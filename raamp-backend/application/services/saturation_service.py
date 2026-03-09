
# Application Layer - Saturation Service
import logging
from typing import List, Dict
import asyncio
from random import uniform
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth
except ImportError:
    stealth = None  # Graceful fallback if playwright_stealth not available

logger = logging.getLogger(__name__)

class SaturationService:
    """
    Service to estimate true market saturation by analyzing:
    1. Google Search Results Count (competition density)
    2. Ad Density (presence of sponsored results)
    3. Trend Maturity (time since peak interest)
    
    Upgraded with Playwright for high stability and stealth.
    
    SCALING NOTE: For industrial-scale scraping (10k+ trends/day), 
    REPLACE this custom Playwright logic with a SERP API (SerpApi, ScraperAPI, ZenRows). 
    These services handle CAPTCHAs and massive proxy rotation at the hardware layer.
    """

    async def _fetch_serp_data_stable(self, keyword: str, max_retries: int = 3) -> Dict:
        """
        Fetch SERP data using Playwright (Stable & Stealth) with retry logic.
        Returns result count and ad count.
        
        Args:
            keyword: Search keyword
            max_retries: Maximum number of retry attempts (default: 3)
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()
                    
                    # Apply stealth to avoid detection
                    if stealth:
                        await stealth(page)
                    
                    logger.info("🔍 Playwright scrape attempt %d/%d for: %s", attempt + 1, max_retries, keyword)
                    
                    try:
                        # Randomized delay to mimic human behavior (longer on retries)
                        delay = uniform(1, 2) + (attempt * 0.5)
                        await asyncio.sleep(delay)
                        
                        url = f"https://www.google.com/search?q={keyword}&hl=en"
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        
                        # 1. Extract Result Count
                        result_count = 0
                        stats_selector = "#result-stats"
                        if await page.query_selector(stats_selector):
                            text = await page.inner_text(stats_selector)
                            import re
                            match = re.search(r'([\d,]+)', text)
                            if match:
                                result_count = int(match.group(1).replace(",", ""))
                        
                        # 2. Extract Ad Count (Top & Bottom ads)
                        ad_selectors = ["[data-text-ad='1']", ".uE1V7b", ".pla-unit"]
                        ad_found = 0
                        for selector in ad_selectors:
                            ads = await page.query_selector_all(selector)
                            ad_found += len(ads)
                        
                        logger.info("✅ Scraping success for '%s' (attempt %d): %d results, %d ads", 
                                  keyword, attempt + 1, result_count, ad_found)
                        
                        return {
                            "result_count": result_count,
                            "ad_count": ad_found,
                            "status": "success"
                        }
                        
                    except Exception as e:
                        last_error = e
                        logger.warning("❌ Scraping failed for '%s' (attempt %d/%d): %s", 
                                     keyword, attempt + 1, max_retries, str(e))
                        
                        # Don't retry if we're on the last attempt
                        if attempt >= max_retries - 1:
                            raise
                            
                    finally:
                        await browser.close()
                        
            except Exception as e:
                last_error = e
                logger.error("Playwright error for '%s' (attempt %d/%d): %s", 
                           keyword, attempt + 1, max_retries, str(e))
                
                # Exponential backoff before retry (but not after last attempt)
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt  # 1s, 2s, 4s
                    logger.info("⏳ Retrying in %ds...", backoff)
                    await asyncio.sleep(backoff)
        
        # All retries exhausted
        logger.error("💥 All %d scraping attempts failed for '%s': %s", max_retries, keyword, last_error)
        return {"result_count": 0, "ad_count": 0, "status": "failed"}

    def calculate_saturation_score(self, interest_level: float, serp_count: int, ad_count: int = 0) -> float:
        """
        Calculate Saturation Score (0-100).
        Includes Ad Density in the calculation.
        """
        # Linear competition factor with 1M as soft cap for niche trends
        competition_factor = min(100, (serp_count / 1_000_000) * 100)
        
        # Ad factor (0-100)
        # 0 ads = 0, 5+ ads = 100
        ad_factor = min(100, (ad_count / 5) * 100)
        
        if serp_count == 0:
            # Fallback if scraping failed
            competition_factor = 50
            ad_factor = 30
            
        # Balanced score: 50% Competition Density, 20% Ad Density, 30% Search Interest
        score = (competition_factor * 0.5) + (ad_factor * 0.2) + (interest_level * 0.3)
        return round(score, 2)

    async def batch_saturation_analysis(self, trends: List[Dict]) -> List[Dict]:
        """
        Analyze a batch of trends for saturation using a shared browser instance for speed.
        """
        results = []
        if not trends:
            return results

        logger.info("BATCH START: Initiating saturation analysis for %d keywords...", len(trends))
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                )
                
                for trend in trends:
                    keyword = trend.get("keyword")
                    interest = trend.get("interest", 50)
                    
                    if not keyword:
                        continue

                    logger.info("BATCH: Analyzing '%s'...", keyword)
                    
                    # Retry logic for each keyword in batch
                    max_retries = 3
                    status = "failed"
                    count = 0
                    ads = 0
                    
                    for attempt in range(max_retries):
                        page = await context.new_page()
                        if stealth:
                            await stealth(page)
                        
                        try:
                            # Randomized delay with backoff on retries
                            delay = uniform(0.5, 1.5) + (attempt * 0.3)
                            await asyncio.sleep(delay)
                            
                            url = f"https://www.google.com/search?q={keyword}&hl=en"
                            await page.goto(url, wait_until="networkidle", timeout=20000)
                            
                            # 1. Extract Result Count
                            stats_selector = "#result-stats"
                            if await page.query_selector(stats_selector):
                                text = await page.inner_text(stats_selector)
                                import re
                                match = re.search(r'([\d,]+)', text)
                                if match:
                                    count = int(match.group(1).replace(",", ""))
                            
                            # 2. Extract Ad Count
                            ad_selectors = ["[data-text-ad='1']", ".uE1V7b", ".pla-unit"]
                            for selector in ad_selectors:
                                try:
                                    ads_els = await page.query_selector_all(selector)
                                    ads += len(ads_els)
                                except Exception:
                                    # Selector not found or query failed, skip it
                                    continue
                            
                            status = "success"
                            logger.info("✅ BATCH scrape success for '%s' (attempt %d): %d results, %d ads", 
                                      keyword, attempt + 1, count, ads)
                            break  # Success, exit retry loop
                            
                        except Exception as e:
                            last_error = e
                            logger.warning("❌ BATCH scrape failed for '%s' (attempt %d/%d): %s", 
                                         keyword, attempt + 1, max_retries, str(e))
                            
                            # Exponential backoff before next retry (but not after last attempt)
                            if attempt < max_retries - 1:
                                backoff = 1.5 ** attempt  # 1.5s, 2.25s, 3.37s
                                logger.info("⏳ Retrying in %.1fs...", backoff)
                                await asyncio.sleep(backoff)
                                
                        finally:
                            await page.close()
                
                    # Fallback if all retries failed
                    is_real = status == "success" and count > 0
                    if not is_real:
                        import random
                        base_competition = interest * 10000 
                        noise = random.uniform(0.5, 2.0)
                        count = int(base_competition * noise)
                        ads = random.randint(0, 3)
                        logger.warning("🔄 BATCH: Using simulation fallback for '%s' after %d failed attempts", 
                                     keyword, max_retries)
                
                    score = self.calculate_saturation_score(interest, count, ads)
                    
                    results.append({
                        "keyword": keyword,
                        "serp_count": count,
                        "ad_count": ads,
                        "saturation_score": score,
                        "ad_density": "HIGH" if ads >= 3 else "MEDIUM" if ads > 0 else "LOW",
                        "is_real_data": is_real
                    })

                await browser.close()
                
            logger.info("BATCH COMPLETE: Processed %d keywords", len(results))
            return results
            
        except (NotImplementedError, RuntimeError, Exception) as e:
            # Playwright failed (common on Windows with certain async loops)
            logger.warning("Playwright initialization failed: %s. Using proxy saturation scores.", str(e))
            
            # Fallback: Generate proxy scores based on search interest
            for trend in trends:
                keyword = trend.get("keyword")
                interest = trend.get("interest", 50)
                
                if not keyword:
                    continue
                
                # Proxy saturation: Higher interest suggests higher saturation
                # Interest 0-30 = Low saturation (20-40)
                # Interest 30-70 = Medium saturation (40-70)
                # Interest 70-100 = High saturation (70-90)
                if interest < 30:
                    proxy_score = 20 + (interest * 0.67)  # 20-40 range
                elif interest < 70:
                    proxy_score = 40 + ((interest - 30) * 0.75)  # 40-70 range
                else:
                    proxy_score = 70 + ((interest - 70) * 0.67)  # 70-90 range
                
                results.append({
                    "keyword": keyword,
                    "serp_count": 0,
                    "ad_count": 0,
                    "saturation_score": round(proxy_score, 2),
                    "ad_density": "UNKNOWN",
                    "is_real_data": False
                })
                
            logger.info("BATCH COMPLETE (PROXY): Generated %d proxy saturation scores.", len(results))
            return results
