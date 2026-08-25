import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from dotenv import load_dotenv

# Find .env in the backend directory
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.from_email = os.getenv("FROM_EMAIL") or "stationeryjunction.jsr@gmail.com"
        self.from_name = os.getenv("FROM_NAME", "Stationery Junction")
        # Handle multiple recipients (comma separated)
        admin_emails_raw = os.getenv("ADMIN_EMAILS", self.smtp_user)
        self.admin_emails = [email.strip() for email in admin_emails_raw.split(",")] if admin_emails_raw else []

    def _resolve_to_emails(self, to_emails: Any) -> list[str]:
        if not to_emails:
            return self.admin_emails
        if isinstance(to_emails, str):
            return [to_emails.strip()]
        return [str(email).strip() for email in to_emails if email]

    def send_email(self, to_emails: Any, subject: str, body: str, html_body: str = None) -> bool:
        """Sends an HTML or plain-text email to one or more recipients."""
        from app.utils.logger import logger

        if not all([self.smtp_host, self.smtp_user, self.smtp_pass]):
            logger.warning("Email configuration missing. Skipping email sending.")
            return False

        to_list = self._resolve_to_emails(to_emails)

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(to_list)
            msg["Subject"] = subject

            # Attach plain text
            msg.attach(MIMEText(body, "plain"))

            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()

            logger.info("Email sent successfully to %s with subject: %s", to_list, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email: %s", str(e), exc_info=True)
            return False

    def send_email_with_attachment(self, to_emails: Any, subject: str, body: str, attachment_path: str):
        """Sends an email with an attachment to one or more recipients."""
        from app.utils.logger import logger

        if not all([self.smtp_host, self.smtp_user, self.smtp_pass]):
            logger.warning("Email configuration missing. Skipping email sending.")
            return False

        to_list = self._resolve_to_emails(to_emails)

        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(to_list)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            filename = os.path.basename(attachment_path)
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            msg.attach(part)

            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()

            logger.info("Email with attachment sent successfully to %s with subject: %s", to_list, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email with attachment: %s", str(e), exc_info=True)
            return False

    def send_error_alert(self, subject: str, body: str, to_emails: Any = None):
        """Simple text-only email for system alerts to one or more recipients."""
        from app.utils.logger import logger
        
        if not all([self.smtp_host, self.smtp_user, self.smtp_pass]):
            logger.warning("Email configuration missing. Skipping error alert sending.")
            return False

        to_list = self._resolve_to_emails(to_emails)

        if not to_list:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(to_list)
            msg["Subject"] = f"[SJ ALERT] {subject}"

            msg.attach(MIMEText(body, "plain"))

            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info("Error alert email sent successfully to %s with subject: %s", to_list, subject)
            return True
        except Exception as e:
            logger.error("Failed to send error alert: %s", str(e), exc_info=True)
            return False

    def send_verification_email(self, to_email: str, code: str) -> bool:
        subject = "Verify your email - Stationery Junction"
        body = f"Your email verification code is: {code}. This code is valid for 15 minutes."
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                <h1 style="color: #3b82f6; margin: 0;">Stationery Junction</h1>
            </div>
            <div style="padding: 20px 0;">
                <p>Hello,</p>
                <p>Thank you for choosing Stationery Junction. Please use the following verification code to verify your email address:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1e3a8a; background: #eff6ff; padding: 10px 20px; border-radius: 6px; border: 1px dashed #3b82f6;">{code}</span>
                </div>
                <p>This code is valid for <strong>15 minutes</strong>. If you did not request this verification, please ignore this email.</p>
            </div>
            <div style="border-top: 1px solid #e0e0e0; padding-top: 10px; font-size: 12px; color: #6b7280; text-align: center;">
                <p>&copy; 2026 Stationery Junction. All rights reserved.</p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body, html_body)

    def send_order_placed_email(self, to_email: str, order: dict) -> bool:
        order_num = order.get("orderNumber") or order.get("_id")
        subject = f"Order Confirmation - {order_num} - Stationery Junction"

        # Build items rows for HTML
        items_html = ""
        items_text = ""
        for item in order.get("items", []):
            prod_name = item.get("product", {}).get("name", "Product")
            qty = item.get("quantity", 0)
            subtotal = item.get("subtotal", 0)
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;">{prod_name}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e0e0e0; text-align: center;">{qty}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e0e0e0; text-align: right;">₹{subtotal:.2f}</td>
            </tr>
            """
            items_text += f"- {prod_name} x {qty}: ₹{subtotal:.2f}\n"

        body = f"Thank you for your order! Your order {order_num} has been placed successfully.\n\nItems:\n{items_text}\nTotal: ₹{order.get('total', 0):.2f}"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="text-align: center; border-bottom: 2px solid #10b981; padding-bottom: 10px;">
                <h1 style="color: #10b981; margin: 0;">Order Confirmed!</h1>
                <p style="color: #6b7280; margin: 5px 0 0 0;">Thank you for shopping with us</p>
            </div>
            <div style="padding: 20px 0;">
                <p>Hello,</p>
                <p>Your order <strong>#{order_num}</strong> has been successfully placed. Here are the details of your order:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background: #f3f4f6;">
                            <th style="padding: 8px; text-align: left;">Item</th>
                            <th style="padding: 8px; text-align: center; width: 80px;">Qty</th>
                            <th style="padding: 8px; text-align: right; width: 100px;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="2" style="padding: 8px; font-weight: bold; text-align: right;">Shipping:</td>
                            <td style="padding: 8px; text-align: right;">₹{order.get("shipping", 0):.2f}</td>
                        </tr>
                        {f'<tr><td colspan="2" style="padding: 8px; font-weight: bold; text-align: right;">Discount:</td><td style="padding: 8px; text-align: right; color: #ef4444;">-₹{order.get("discount"):.2f}</td></tr>' if order.get("discount", 0) > 0 else ""}
                        <tr style="font-size: 18px; font-weight: bold;">
                            <td colspan="2" style="padding: 8px; text-align: right; border-top: 2px solid #e0e0e0;">Total:</td>
                            <td style="padding: 8px; text-align: right; border-top: 2px solid #e0e0e0; color: #10b981;">₹{order.get("total", 0):.2f}</td>
                        </tr>
                    </tfoot>
                </table>
                
                <p>We are processing your order and will notify you when it ships.</p>
            </div>
            <div style="border-top: 1px solid #e0e0e0; padding-top: 10px; font-size: 12px; color: #6b7280; text-align: center;">
                <p>&copy; 2026 Stationery Junction. All rights reserved.</p>
            </div>
        </div>
        """

        # Attach invoice PDF if generated
        invoice_path = order.get("invoicePath")
        if invoice_path and os.path.exists(invoice_path):
            return self.send_email_with_attachment(to_email, subject, body, invoice_path)

        return self.send_email(to_email, subject, body, html_body)

    def send_order_delivered_email(self, to_email: str, order: dict) -> bool:
        order_num = order.get("orderNumber") or order.get("_id")
        subject = f"Order Delivered - {order_num} - Stationery Junction"
        body = f"Great news! Your order {order_num} has been delivered successfully. Thank you for shopping at Stationery Junction!"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                <h1 style="color: #3b82f6; margin: 0;">Order Delivered!</h1>
            </div>
            <div style="padding: 20px 0;">
                <p>Hello,</p>
                <p>Your order <strong>#{order_num}</strong> has been successfully delivered to your shipping address.</p>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center; color: #166534; font-weight: bold;">
                    Order Delivered Successfully
                </div>
                <p>We hope you enjoy your stationery! If you have any questions or feedback, please contact our support team.</p>
            </div>
            <div style="border-top: 1px solid #e0e0e0; padding-top: 10px; font-size: 12px; color: #6b7280; text-align: center;">
                <p>&copy; 2026 Stationery Junction. All rights reserved.</p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body, html_body)

    def send_privacy_policy_update_email(
        self, to_email: str, last_updated: str, policy_url: str, version: str = "1.0"
    ) -> bool:
        """Notify a user that the Privacy Policy has been updated."""
        subject = f"Important: Our Privacy Policy Has Been Updated (Version {version}) - Stationery Junction"
        body = (
            f"Dear Customer,\n\n"
            f"We wanted to let you know that our Privacy Policy has been updated to Version {version}"
            f"{(' (effective ' + last_updated + ')') if last_updated else ''}.\n\n"
            f"Please take a moment to review the changes at:\n{policy_url}\n\n"
            f"By continuing to use our services, you agree to the updated Privacy Policy.\n\n"
            f"If you have any questions, please contact us at {self.from_email}.\n\n"
            f"Thank you for being a valued customer.\n\n"
            f"The Stationery Junction Team"
        )
        updated_label = f"Effective: {last_updated}" if last_updated else "Recently Updated"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 16px; margin-bottom: 24px;">
                <h1 style="color: #1e3a8a; margin: 0 0 4px 0;">Stationery Junction</h1>
                <p style="color: #6b7280; margin: 0; font-size: 13px;">Privacy Policy Update</p>
            </div>
            <div style="padding: 0 0 20px 0;">
                <p style="margin-top: 0;">Dear Customer,</p>
                <p>We are writing to let you know that we have updated our <strong>Privacy Policy</strong>.</p>

                <!-- Version badge -->
                <div style="display: flex; align-items: center; gap: 12px; margin: 20px 0;">
                    <span style="background: #1e3a8a; color: #ffffff; font-size: 13px; font-weight: bold;
                                 padding: 5px 14px; border-radius: 20px; white-space: nowrap;">
                        Version {version}
                    </span>
                    <span style="color: #6b7280; font-size: 13px;">{updated_label}</span>
                </div>

                <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 18px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; color: #1e3a8a; font-weight: bold;">What has changed?</p>
                    <p style="margin: 8px 0 0 0; color: #374151; font-size: 14px;">
                        We have made updates to our Privacy Policy to better reflect how we collect, use, and protect your data.
                        Please review the full policy to understand how these changes may affect you.
                    </p>
                </div>

                <div style="text-align: center; margin: 28px 0;">
                    <a href="{policy_url}"
                       style="background: #1e3a8a; color: #ffffff; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 15px; display: inline-block;">
                        View Privacy Policy v{version}
                    </a>
                </div>
                <p style="font-size: 13px; color: #6b7280;">
                    By continuing to use Stationery Junction, you acknowledge and agree to the updated Privacy Policy.
                    If you have any questions, please reach out to us at
                    <a href="mailto:{self.from_email}" style="color: #3b82f6;">{self.from_email}</a>.
                </p>
            </div>
            <div style="border-top: 1px solid #e0e0e0; padding-top: 12px; font-size: 12px; color: #9ca3af; text-align: center;">
                <p style="margin: 0;">&copy; 2026 Stationery Junction. All rights reserved.</p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body, html_body)

    def send_order_returned_email(self, to_email: str, return_request: dict) -> bool:
        order_id = return_request.get("orderId")
        return_num = return_request.get("_id")
        subject = f"Return Completed - Return #{return_num} - Stationery Junction"
        body = f"Your return request for order {order_id} has been processed and completed successfully."
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="text-align: center; border-bottom: 2px solid #ef4444; padding-bottom: 10px;">
                <h1 style="color: #ef4444; margin: 0;">Return Completed</h1>
            </div>
            <div style="padding: 20px 0;">
                <p>Hello,</p>
                <p>Your return request <strong>#{return_num}</strong> for order <strong>#{order_id}</strong> has been successfully completed.</p>
                <p>The returned items have been restocked, and any refunds/credit adjustments have been processed.</p>
            </div>
            <div style="border-top: 1px solid #e0e0e0; padding-top: 10px; font-size: 12px; color: #6b7280; text-align: center;">
                <p>&copy; 2026 Stationery Junction. All rights reserved.</p>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, body, html_body)


email_service = EmailService()
