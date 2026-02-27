# Discord Webhook Setup (WishlistOps)

WishlistOps uses a Discord **webhook** (not login) to send drafts into a channel for approval.

## Create a webhook
1. Open your Discord server.
2. Go to **Server Settings → Integrations → Webhooks**.
3. Click **New Webhook**.
4. Choose the target channel (e.g. `#wishlistops-approvals`).
5. Click **Copy Webhook URL**.

## Add it to WishlistOps
- Open the WishlistOps dashboard (`setup` command).
- Go to **API Keys**.
- Paste the webhook URL into **Discord Webhook**.
- Click **Save**.
- Click **Test Connection** (you’ll be asked to confirm before it sends a message).

## Notes
- Keep your webhook URL secret.
- If you rotate/delete the webhook in Discord, you must paste the new URL into the dashboard.
