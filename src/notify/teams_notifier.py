import requests
import json
import os
import datetime

def send_teams_notification(metrics, summary_text, error_count, execution_time):
    """
    Sends a formatted Adaptive Card to Microsoft Teams webhook 
    to notify the Finance Board of the Daily Closing.
    """
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("TEAMS_WEBHOOK_URL not configured. Skipping MS Teams notification.")
        return False
        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Status coloring
    status_color = "00FF00" if error_count == 0 else "FF0000"
    compliance_text = "PASSED" if error_count == 0 else f"FAILED ({error_count} Divergencies)"
    
    card_payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": status_color,
        "summary": "Infios Finance OS - Daily Closing",
        "sections": [{
            "activityTitle": f"📊 Infios Finance OS: Executive Summary ({date_str})",
            "activitySubtitle": f"Architect: Magno Freitas | Execution Latency: {execution_time:.2f}s",
            "facts": [
                {"name": "Compliance Status", "value": compliance_text},
                {"name": "Account 41.000 Revenue", "value": f"R$ {metrics.get('rr_credit_41000', 0):,.2f}"},
                {"name": "Account 41.000 Reversals", "value": f"R$ {metrics.get('reversal_debit_41000', 0):,.2f}"},
                {"name": "Foreign Exchange Variances", "value": f"R$ {metrics.get('variacao_cambial', 0):,.2f}"}
            ],
            "markdown": True
        }],
        "potentialAction": [{
            "@type": "OpenUri",
            "name": "View AI Summary (Vertex)",
            "targets": [{"os": "default", "uri": "https://console.cloud.google.com/vertex-ai"}]
        }]
    }

    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(card_payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            print("Successfully sent Executive Summary to MS Teams via Webhook.")
            return True
        else:
            print(f"Failed to push to Teams. HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error publishing to Teams: {e}")
        return False
