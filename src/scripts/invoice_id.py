import datetime
import uuid

class InvoiceNumberGenerator:
    def _base36_short_random(self, length: int = 4) -> str:
        n = uuid.uuid4().int >> 96
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
        out = []
        for _ in range(length):
            n, r = divmod(n, 36)
            out.append(alphabet[r])
        return "".join(reversed(out)).upper()

    def generate_invoice_number_quick(self,counter: int, date) -> str:
        """
        Stateless generator. You must provide a counter (persisted elsewhere).
        Example: generate_invoice_number_quick(counter=123) -> '20250819-000123-7X4B'
        """
        today = datetime.date.today().strftime("%Y%m%d")
        seq_part = f"{counter:06d}"
        rand = self._base36_short_random(4)
        return f"{date}-{seq_part}-{rand}"

    def generate_invoice_uuid(self) -> str:
        return str(uuid.uuid4())
    
    def generate_invoice_number(self, counter: int, date) -> str:
        inv_num = self.generate_invoice_number_quick(counter, date)
        inv_uuid = self.generate_invoice_uuid()
        return {"num": inv_num, "uuid": inv_uuid}