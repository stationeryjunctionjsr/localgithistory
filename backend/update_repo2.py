with open('app/repositories/support_ticket_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_add = '''    async def addResponse(self, ticket_id: str, user: str, message: str, attachments: list[str], is_admin_response: bool) -> SupportTicketInternal:
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_resp = TicketResponseItemInternal(user=user, message=message, attachments=attachments)

        responses: list[TicketResponseItemInternal] = []
        if ticket.responses:
            for r in ticket.responses:
                responses.append(TicketResponseItemInternal(user=r.user, message=r.message, attachments=r.attachments))'''

new_add = '''    async def addResponse(self, ticket_id: str, user: str, message: str, attachments: list[str], is_admin_response: bool) -> SupportTicketInternal:
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_resp = TicketResponseItemInternal(user=user, message=message, attachments=attachments, isAdminResponse=is_admin_response)

        responses: list[TicketResponseItemInternal] = []
        if ticket.responses:
            for r in ticket.responses:
                responses.append(TicketResponseItemInternal(user=r.user, message=r.message, attachments=r.attachments, isAdminResponse=r.isAdminResponse))'''

if old_add in text:
    text = text.replace(old_add, new_add)
else:
    print("Could not find old_add")

with open('app/repositories/support_ticket_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
