class Economy:
    """
    Reprezentuje ekonomiku hry.
    """
    def __init__(self, initial_balance: float):
        """
        Inicializuje ekonomiku s počátečním zůstatkem.
        
        Args:
            initial_balance (float): počáteční peníze
        """
        self.balance = initial_balance

    def can_afford(self, amount: float) -> bool:
        """
        Zkontroluje, zda si může dovolit utratit danou částku.
        """
        return self.balance >= amount

    def deduct(self, amount: float):
        """
        Strhne peníze ze zůstatku.
        """
        self.balance -= amount

    def add(self, amount: float):
        """
        Přidá peníze do zůstatku.
        """
        self.balance += amount
        