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


## Ovládání

### Stavba tratí

- **klávesa `T`** aktivuje režim stavby, opětovný stisk zruší rozpracovanou trať
- **klávesa `Z`** během stavby tratě smaže naposledy přidaný bod
- **levé tlačítko myši** do kolejové trati přidává body
- první i poslední bod musí být umístěn na zastávce, jinak trať nelze dokončit

### Plánování spojů

- **klávesa `R`** aktivuje režim plánování spojů, opětovný stisk zruší rozpracovaný spoj
- **klávesa `Z`** během plánování spoje smaže naposledy přidanou zastávku
- **levé tlačítko myši** přidává další zastávku do rozpracovaného spoje (stanice musí být propojeny tratí)
- **pravé tlačítko myši** dokončí navržený spoj a otevře menu pro výběr a nasazení vlakové soupravy

### Správa vlaků a inventář (menu)

- **klávesa `M`** otevře/zavře menu (lze zavřít i klávesou `ESC`)
- z nabídky lze nakupovat lokomotivy a vagony
- zakoupená vozidla se ukládají do inventáře, ze kterého je lze následně sestavovat do vlakových souprav

### Čas

- **klávesa `P`** pozastaví nebo opětovně spustí běh herního času


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
Velikost pixelu použitých ortofot ČR je `0.125 m`, tzn. `1 m = 8 px`.

### Časové měřítko
1 reálná sekunda odpovídá 3 ingame minutám.

### Fyzikální jednotky v kódu
- rychlost (`max_speed`): km/h
- výkon lokomotivy (`power`): kW
- kapacita nákladu (`cargo_capacity`): t

### Seznam měst s železničními stanicemi
Dostupný [zde](https://provoz.spravazeleznic.cz/portal/ViewArticle.aspx?oid=34462).


## TODO