import urllib.request
import os

# --- CONFIGURATION (LAYER 0 DNS GENERATOR) ---
# We are combining the most powerful community lists for a school environment.
# This generates a standard "domains-only" text file compatible with enterprise 
# DNS servers (Pi-hole, NextDNS, Cloudflare Zero Trust, AdGuard, etc.).

URLS = [
    # StevenBlack's Comprehensive (Ads, Malware, Fake News, Gambling, NSFW, Social)
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn-social/hosts",
    # OISD Big (Ads, Telemetry, Phishing, Malware)
    "https://big.oisd.nl/",
    # OISD NSFW (Inappropriate content / Strict CIPA compliance)
    "https://nsfw.oisd.nl/"
]

LOCAL_BLOCKS_FILE = "school_forced_blocks.txt"
OUTPUT_FILE = "dns_blocklist.txt"

def fetch_and_extract_domains(url):
    print(f"Downloading from: {url}")
    domains = set()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            raw_data = response.read().decode('utf-8')
            
        for line in raw_data.splitlines():
            # 1. Chop off any inline comments (anything after a '#')
            clean_line = line.split('#')[0].strip()
            
            # 2. Skip if the line is now empty
            if not clean_line:
                continue
            
            # 3. Handle both StevenBlack ("0.0.0.0 domain.com") and OISD ("domain.com") formats
            parts = clean_line.split()
            if not parts:
                continue
                
            domain = parts[-1].lower()
            
            # 4. Filter out local loopbacks and system hosts
            if domain not in ['localhost', '127.0.0.1', '0.0.0.0', 'broadcasthost']:
                # Double-check it doesn't have weird characters left over
                if '[' not in domain and ']' not in domain:
                    domains.add(domain)
                
        print(f" -> Extracted {len(domains)} unique domains from this list.")
        return domains
        
    except Exception as e:
        print(f" -> Error downloading or parsing {url}: {e}")
        return set()

if __name__ == "__main__":
    print("--- Glassbox DNS Blocklist Generator (Layer 0) ---")
    all_unique_domains = set()
    
    for url in URLS:
        # Fetch domains from each list
        domains = fetch_and_extract_domains(url)
        
        # .update() merges the sets and automatically drops any duplicates!
        all_unique_domains.update(domains) 

    # --- NEW: Process local forced blocks file ---
    if os.path.exists(LOCAL_BLOCKS_FILE):
        print(f"\nFound local override file: {LOCAL_BLOCKS_FILE}. Merging...")
        try:
            with open(LOCAL_BLOCKS_FILE, 'r') as f:
                local_domains = set()
                for line in f:
                    clean_line = line.split('#')[0].strip()
                    if clean_line:
                        local_domains.add(clean_line.lower())
            all_unique_domains.update(local_domains)
            print(f" -> Added {len(local_domains)} custom domains from local file.")
        except Exception as e:
            print(f" -> Error reading local file: {e}")
    else:
        print(f"\nNo local override file ({LOCAL_BLOCKS_FILE}) found. Skipping.")
        
    print(f"\nTotal unique domains combined: {len(all_unique_domains)}")
    
    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        # Sort the domains alphabetically for a clean, organized output file
        for domain in sorted(all_unique_domains):
            f.write(f"{domain}\n")
            
    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"✅ Success! Saved {OUTPUT_FILE} ({file_size_mb:.2f} MB)")
    print("This file is ready to be imported into your school's custom DNS server!")
