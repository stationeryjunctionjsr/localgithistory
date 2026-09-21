with open('app/repositories/support_ticket_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_add_response = '''    async def addResponse(self, ticket_id: str, user: str, message: str, is_admin_response: bool) -> SupportTicketInternal:
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_resp = TicketResponseItemInternal(user=user, message=message)

        responses: list[TicketResponseItemInternal] = []
        if ticket.responses:
            for r in ticket.responses:
                responses.append(TicketResponseItemInternal(user=r.user, message=r.message))

        responses.append(new_resp)'''

new_add_response = '''    async def addResponse(self, ticket_id: str, user: str, message: str, attachments: list[str], is_admin_response: bool) -> SupportTicketInternal:
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_resp = TicketResponseItemInternal(user=user, message=message, attachments=attachments)

        responses: list[TicketResponseItemInternal] = []
        if ticket.responses:
            for r in ticket.responses:
                responses.append(TicketResponseItemInternal(user=r.user, message=r.message, attachments=r.attachments))

        responses.append(new_resp)'''

if old_add_response in text:
    text = text.replace(old_add_response, new_add_response)
else:
    print("Could not find addResponse method to replace")

with open('app/repositories/support_ticket_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
