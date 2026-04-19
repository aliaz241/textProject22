import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import sys # برای استفاده از sys.exit

DATA_FILE = "data.json"

# ================= LOAD OLD DATA =================
def load_old_data():
    """
    Loads existing messages from DATA_FILE.
    Returns an empty list if the file doesn't exist, is empty, or is corrupted.
    Exits the program if critical errors occur during loading.
    """
    if not os.path.exists(DATA_FILE):
        print(f"'{DATA_FILE}' not found. Starting with an empty message list.")
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                print(f"'{DATA_FILE}' is empty. Starting with an empty message list.")
                return []
            
            data = json.loads(content)
            # Ensure the loaded data has a 'messages' key, default to empty list if not
            if "messages" not in data:
                 print(f"Warning: '{DATA_FILE}' does not contain a 'messages' key. Assuming empty list.")
                 return []
            return data.get("messages", [])
            
    except json.JSONDecodeError:
        print(f"CRITICAL ERROR: Could not decode JSON from '{DATA_FILE}'. File might be corrupted.")
        # Backup corrupted file before exiting
        try:
            backup_name = f"{DATA_FILE}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(DATA_FILE, backup_name)
            print(f"Corrupted file backed up as '{backup_name}'.")
        except Exception as backup_e:
            print(f"Failed to back up corrupted file: {backup_e}")
        sys.exit(1) # Exit program on critical JSON error
    except IOError as e:
        print(f"CRITICAL ERROR: Could not read file '{DATA_FILE}'. Reason: {e}")
        sys.exit(1) # Exit program on critical IO error
    except Exception as e:
        print(f"CRITICAL ERROR: An unexpected error occurred while loading data: {e}")
        sys.exit(1) # Exit program on other critical errors


# ================= SAVE DATA =================
def save_data(data):
    """
    Saves the provided data (expected to be a list of messages) to DATA_FILE.
    Uses indent=4 for pretty printing and ensure_ascii=False for proper UTF-8 encoding.
    Exits the program if saving fails.
    """
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"messages": data}, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(data)} messages to '{DATA_FILE}'.")
    except IOError as e:
        print(f"CRITICAL ERROR: Could not write to file '{DATA_FILE}'. Reason: {e}")
        sys.exit(1) # Exit if we cannot save the data
    except Exception as e:
        print(f"CRITICAL ERROR: An unexpected error occurred while saving data: {e}")
        sys.exit(1) # Exit on other critical errors


# ================= GET POSTS =================
def get_last_posts(channel):
    """
    Fetches the last 3 posts from a given Telegram channel's public page.
    Returns a list of dictionaries, each representing a post.
    Returns an empty list if errors occur during fetching or parsing, and prints the error.
    """
    url = f"https://t.me/s/{channel}"
    print(f"Fetching posts from: {url}")
    
    try:
        response = requests.get(url, timeout=15) 
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        soup = BeautifulSoup(response.text, "html.parser")
        posts = soup.find_all("div", class_="tgme_widget_message")
        print(f"Found {len(posts)} potential message elements on the page for channel '{channel}'.")

        results = []
        # Process only the last 3 found posts
        for post in posts[-3:]:
            text_el = post.find("div", class_="tgme_widget_message_text")
            text = text_el.get_text(" ", strip=True) if text_el else ""

            img_el = post.find("img")
            image = img_el["src"] if img_el and "src" in img_el.attrs else None

            time_el = post.find("time")
            # Ensure datetime is correctly parsed or use current UTC time as fallback
            time_str = datetime.utcnow().isoformat() + "Z" # Default to current UTC
            if time_el and "datetime" in time_el.attrs:
                 try:
                     # Attempt to parse the datetime attribute for validation
                     datetime.fromisoformat(time_el["datetime"].replace('Z', '+00:00'))
                     time_str = time_el["datetime"]
                 except ValueError:
                     print(f"Warning: Invalid datetime format found in post for channel '{channel}'. Using current UTC time.")
            
            results.append({
                "channel": channel,
                "text": text,
                "image": image,
                "time": time_str
            })
            
        print(f"Successfully extracted {len(results)} posts from channel '{channel}'.")
        return results

    except requests.exceptions.Timeout:
        print(f"ERROR: Request timed out while fetching {url}")
        return [] # Return empty list, but error is logged
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error occurred for {url}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"ERROR: A network-related error occurred while fetching {url}: {e}")
        return []
    except Exception as e:
        # Catch any other unexpected errors during parsing
        print(f"ERROR: An unexpected error occurred while processing channel '{channel}': {e}")
        return []


# ================= MAIN =================
def main():
    print("--- Starting Telegram Data Reader ---")
    
    # Define channels directly in the code
    # <<<==== کانال‌های مورد نظر خود را اینجا وارد کنید ====>>>
    channels_to_read = ["telegram", "some_other_channel"] 
    
    # --- Check if channel list is empty ---
    if not channels_to_read:
        print("ERROR: No channels defined in 'channels_to_read'. Please add channel names.")
        sys.exit(1)
    if all(ch.strip() == "" for ch in channels_to_read):
         print("ERROR: All defined channels are empty strings. Please add valid channel names.")
         sys.exit(1)
    
    # --- Load existing data ---
    old_messages = load_old_data()
    
    # --- Collect new messages ---
    new_messages_collected = []
    for ch in channels_to_read:
        if ch.strip(): # Process only if channel name is not empty
            posts = get_last_posts(ch)
            # get_last_posts already prints errors, so we just extend the list
            new_messages_collected.extend(posts)

    # --- Combine and save data ---
    # Simple concatenation. For de-duplication, more advanced logic is needed.
    all_messages = old_messages + new_messages_collected
    save_data(all_messages) # save_data will exit if it fails

    # --- Summary ---
    print("\n--- Process Summary ---")
    print(f"Number of new messages fetched: {len(new_messages_collected)}")
    print(f"Total messages in '{DATA_FILE}' after update: {len(all_messages)}")

    if new_messages_collected:
        print("\n--- Preview of newly added messages (first 5) ---")
        # Use json.dumps for pretty printing the preview
        print(json.dumps(new_messages_collected[:5], indent=2, ensure_ascii=False))
        if len(new_messages_collected) > 5:
            print("...")
    else:
        print("No new messages were fetched in this run.")
        
    print("--- Telegram Data Reader finished successfully ---")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        # Catch SystemExit specifically to indicate that the program exited intentionally due to an error
        print(f"Program exited with code: {e.code}")
        # No need to print additional error messages here as they are printed within the functions before sys.exit()
    except Exception as e:
        # Catch any other unexpected exceptions that weren't caught by sys.exit()
        print(f"CRITICAL UNCAUGHT ERROR: An unexpected error occurred: {e}")
        # Optionally, print traceback here for debugging
        # import traceback
        # traceback.print_exc()
        sys.exit(1) # Ensure a non-zero exit code for any uncaught errors
