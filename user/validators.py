from django.core.validators import RegexValidator


class MobileNumberValidator(RegexValidator):
    """
        Mobile Number validation with or without +977 for Nepal country code, starting with 9.
        Args:
            RegexValidator ([regex]): Regex pattern for mobile number for Nepal
    """
    regex = '^(\+*977[- ]?)?[9](\d{9})$'
    message = (
        'Invalid Mobile Number. Valid Eg.: +977-9812345678 /+977 9876541233/977-9812345678/9874563201')
