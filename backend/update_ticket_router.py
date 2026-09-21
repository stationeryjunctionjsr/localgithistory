with open('app/routers/support_tickets.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_call = '''    await support_ticket_repository.addResponse(
        ticket_id,
        {
            "user": current_user.id,
            "message": response_data.message,
            "attachments": response_data.attachments or [],
            "isAdminResponse": is_admin_response,
        },
    )'''

new_call = '''    await support_ticket_repository.addResponse(
        ticket_id=ticket_id,
        user=current_user.id,
        message=response_data.message,
        attachments=response_data.attachments or [],
        is_admin_response=is_admin_response,
    )'''

if old_call in text:
    text = text.replace(old_call, new_call)
else:
    print("Could not find addResponse call to replace")

with open('app/routers/support_tickets.py', 'w', encoding='utf-8') as f:
    f.write(text)
