# Terminus

## Instalace

```
git clone https://github.com/matee28/Terminus
cd Terminus
pip install -e .
```
Po instalaci lze hru (zatím pouze testovací verzi) spustit příkazem:
```
terminus-test
```


## Specifikace projektu


### Základní idea

Terminus je simulátor železničního magnáta.

Hráč se pohybuje na 2D mapě s náhodně vygenerovanými městy, mezi kterými staví potřebné vlakové tratě. Musí vybudovat stabilní železniční infrastrukturu a zároveň efektivně nakládat s finančními prostředky. Hráč si také spravuje inventář lokomotiv a vagonů, které postupně vylepšuje a skládá z nich vhodné vlakové soupravy.


### Implementace

- Hra je postavena na principech OOP. Vlastnosti lokomotiv, vagonů, měst, zastávek atd. jsou vedeny ve třídách.
- Vlastní engine (TerminusEngine) postavený na knihovně Pygame zajišťuje jednoduchou správu herní smyčky a eventů a simuluje provoz vlaků.
- Data o postupu ve hře jsou ukládány do JSON souborů.


### Interface

2D grafické rozhraní běžící v Pygame okně. Hra je ovládána myší a klávesnicí.


### Použité knihovny

- pygame
- json
- random



## Poznámky

### Měřítko
Velikost pixelu ortofot ČR je `0.125 m`, tzn. `1 m = 8 px`.