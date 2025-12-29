from django.core.mail.backends.console import EmailBackend

class SimpleConsoleEmailBackend(EmailBackend):
    def write_message(self, message):
        print("\n" + "="*40)
        print(f"Subject: {message.subject}")
        print(f"To: {', '.join(message.to)}")
        print("-" * 40)
        print(message.body)
        print("=" * 40 + "\n")
