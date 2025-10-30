from urllib.parse import urlparse
import functools

# List of excluded patterns (you should define your actual list)
excluded_patterns = [
    # Account, Profile, and Membership Management
    "account", "login", "membership", "register", "logout", "profile", "settings", "dashboard", "password", 
    "verify", "confirm", "reset", "admin", "checkout", "cart", "payment", "order", "thank-you", "terms", 
    "privacy", "cookie-policy", "faq", "support", "help", "user", "profile-edit", "subscription", "billing", 
    "invoice", "purchase", "membership-plans", "referral", "offer", "promo", "coupons", "redeem", "feedback", 
    "survey", "testimonials", "contact", "unsubscribe", "error", "404", "500", "maintenance", "coming-soon", 
    "search", "results", "admin-login", "upload", "downloads", "api", "robots.txt", "terms-of-service", 
    "privacy-policy", "forgot-password", "reset-password", "dashboard", "my-account", "orders", "payments", 
    "checkout", "cart", "login", "sign-up", "logout", "admin-dashboard", "client-login", "user-login", 
    "admin-panel", "admin-area", "user-profile", "change-password", "forgot-password", "user-settings", 
    "privacy-policy", "terms-and-conditions", "unsubscribe-newsletter", "purchase-history", "user-orders", 
    "shipping", "account-settings", "my-orders", "account-overview", "view-profile", "account-details", 
    "purchase-summary", "user-dashboard", "payment-history", "admin-login", "client-area", "account-management", 
    "user-management", "membership-area", "membership-dashboard", "user-profile-edit", "terms-of-use", 
    "contact-us", "support-us", "feedback-survey", "coupon-code", "order-summary", "checkout-complete", 
    "store-locator", "order-tracking", "shipping-details", "cart-items", "account-info", "user-info", 
    "confirm-order", "coupon", "reward", "feedback", "order-history", "sign-in", "sign-out", "login-signup", 
    "terms-policy", "privacy-settings", "order-receipt", "tracking", "order-tracking", "user-details", 
    "user-info", "reset-password-link", "logout-success", "purchase-status",

    # Additional Exclusions
    "user-login", "user-signup", "account-creation", "profile-update", "profile-settings", "account-verification", 
    "payment-methods", "transaction-history", "payment-status", "payment-failed", "purchase-confirmation", 
    "order-confirmation", "order-cancelled", "purchase-completed", "accept-terms", "terms-acceptance", "agreement", 
    "policy-acceptance", "sign-terms", "user-agreement", "agreement-confirmation", "agreement-acceptance", 
    "404-error", "error-page", "internal-error", "server-error", "not-found", "offline", "page-not-found", "auth", 
    "oauth", "access-denied", "login-failed", "login-redirect", "verify-email", "confirm-email", "cookie-consent", 
    "cookie-settings", "cookies", "privacy-preferences", "cookie-policy-agreement", "privacy-settings", 
    "cookie-banner", "admin-console", "admin-settings", "admin-tools", "user-management", "admin-users", 
    "admin-panel", "localization", "language-settings", "locale", "timezone", "country-selection", "geo-location", 
    "redirect", "referral-link", "paypal", "stripe", "payment-gateway", "payment-processing", "payment-receipt", 
    "transaction-summary", "billing-info", "subscription-details", "order-status", "subscription-info", 
    "order-tracking", "delivery-status", "tracking-number", "order-details", "price-breakdown", "price-details", 
    "promo-codes"
]

# List of irrelevant domains (you should define your actual list)
irrelevant_domains = [
    "example.com", "test.com", "localhost", "127.0.0.1", "dev.local", "local", "myapp.local", "staging.example.com", 
    "invalid.com", "example.org", "example.net", "localdomain", "site.test", "test.local", "invalid.org", 
    "invalid.net", "localhost.localdomain", "*.localhost", "*.dev", "*.local", "*.test", "*.example", "*.example.net", 
    "localhost.com", "testsite.com", "foobar.local", "demo.local", "local.example", "randomtest.com", "tld.test", 
    "xyz.test", "mytestsite.com", "testingdomain.com", "sandbox.local", "staging.local", "mockdomain.com", 
    "testing.local", "site.local", "test123.com", "localhost.xyz", "localhost.local", "temporary.com", 
    "testing.example", "nonexistent.local", "invalid-domain.local"
]

def get_domain(url):
    protocol_sep = "://"
    if protocol_sep in url:
        url = url.split(protocol_sep)[1]
    return url.split("/")[0]

# A simple function to normalize a URL (you can improve this if needed)
def normalize_url(url):
    return urlparse(url)._replace(fragment='').geturl()

# A simple function to extract the domain
def get_domain(url):
    return urlparse(url).hostname

# A function to get the path and query of a URL
def get_path_and_query(url):
    parsed_url = urlparse(url)
    return parsed_url.path + ("?" + parsed_url.query if parsed_url.query else "")

def is_valid_url(url, url_to_crawl):
    try:
        base_domain = get_domain(url_to_crawl)

        # Check for unsupported link schemes or malformed URLs
        if not url or (not url.startswith("http") and not url.startswith("https://")):
            return False

        parsed_url = urlparse(url)

        # Check for javascript links
        if url.startswith("javascript:") or parsed_url.scheme == "javascript":
            return False

        # Check for mailto links
        if url.startswith("mailto:") or parsed_url.scheme == "mailto":
            return False

        # Check for unscrappable content based on excluded patterns
        if any(pattern.lower() in parsed_url.geturl().lower() for pattern in excluded_patterns):
            return False

        # Check for anchor links (e.g., #home, #about)
        if "#" in url or parsed_url.fragment:
            return False

        # Check for file extensions that are not relevant (PDFs, images, archives, etc.)
        unsupported_file_types = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".zip", ".tar", ".gz"]
        if any(url.endswith(extension) for extension in unsupported_file_types):
            return False

        # Block irrelevant domains
        if parsed_url.hostname in irrelevant_domains:
            return False

        link_domain = get_domain(url)
        base_link = normalize_url(url)
        base_crawl = normalize_url(url_to_crawl)
        path_and_query = get_path_and_query(url)

        return base_link != base_crawl and link_domain == base_domain and bool(path_and_query)
    
    except Exception as e:
        return False

def try_except_decorator(identifier=""):
    def decorator(func):  # Now this function correctly wraps another function
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            state = kwargs.get("state") or args[0] if args else None
            try:
                return func(*args, **kwargs)
            except Exception as e:
                message = f"Error in {identifier} node: {str(e)}"
                if state is not None:
                    state["error"] = message
                    state["failed_node"] = identifier

                return state
        return wrapper
    return decorator  # Return the actual decorator function
