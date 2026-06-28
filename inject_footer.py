import sqlite3
import os
import base64

def inject():
    db_path = 'one-api.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Read the pure JS from the workspace directory
    js_path = os.path.join(os.path.dirname(__file__), 'inject.js')
    if not os.path.exists(js_path):
        print(f"Error: {js_path} not found.")
        return
        
    with open(js_path, 'r', encoding='utf-8') as f:
        js_code = f.read()
        
    print(f"JS code length: {len(js_code)}")
    
    # Base64 encode the raw JS
    b64_bytes = base64.b64encode(js_code.encode('utf-8'))
    b64_str = b64_bytes.decode('utf-8')
    
    # Wrap in img onerror eval with TextDecoder to support Chinese characters and prevent quote breaking in HTML attributes
    injected_html = f'<img src="x" onerror="eval(new TextDecoder().decode(Uint8Array.from(atob(\'{b64_str}\'), c => c.charCodeAt(0))))" style="display:none;">'
    
    c.execute("INSERT OR REPLACE INTO options (key, value) VALUES ('Footer', ?)", (injected_html,))
    conn.commit()
    print("Successfully injected Base64 JS code into Footer option!")
    conn.close()

if __name__ == '__main__':
    inject()
