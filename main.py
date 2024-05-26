import dht  # Importuje knihovnu dht pro práci s DHT11 senzorem
import machine  # Importuje knihovnu machine pro práci s hardwarem ESP32
import network  # Importuje knihovnu network pro práci s WiFi
import socket  # Importuje knihovnu socket pro práci s TCP/IP protokolem
import time  # Importuje knihovnu time pro práci s časem

# Nastavení pinů pro tlačítko a LED diody
tlacitko_reset = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)  # Nastaví pin 5 jako vstupní pin s pull-up rezistorem
led1 = machine.Pin(2, machine.Pin.OUT)  # Nastaví pin 2 jako výstupní pin
led2 = machine.Pin(3, machine.Pin.OUT)  # Nastaví pin 3 jako výstupní pin

rele_in = machine.Pin(21, machine.Pin.OUT)  # Nastaví pin 21 jako výstupní pin
ovladani = 0  # Vytvoří proměnnou ovladani a nastaví její hodnotu na 0

rele_in.value(0)  # Nastaví hodnotu pinu pro relé na 0 (vypne relé)

def resetovat_zarizeni(cislo_pinu):  # Definuje funkci resetovat_zarizeni s parametrem cislo_pinu
    # Pokud je tlačítko stisknuto, zařízení se resetuje
    if cislo_pinu.value() == 0:  # Pokud je hodnota pinu 0 (tlačítko je stisknuto)
        machine.reset()  # Resetuje zařízení

# Nastavení přerušení pro tlačítko
tlacitko_reset.irq(trigger=machine.Pin.IRQ_FALLING, handler=resetovat_zarizeni)  # Nastaví přerušení pro tlacitko_reset, které se spustí při sestupné hraně signálu (tlačítko je stisknuto) a zavolá funkci resetovat_zarizeni

wlan = network.WLAN(network.STA_IF)  # Vytvoří instanci třídy WLAN
wlan.active(True)  # Aktivace WiFi
wlan.connect('Název_sítě', 'Heslo')  # Připojení k WiFi síti

while wlan.status() != 3:  # Čekání na připojení k WiFi síti
    print('waiting for connection...')
    led2.on()  # LED2 svítí, když zařízení není připojeno
    led1.off()  # LED1 nesvítí, když zařízení není připojeno
    time.sleep(2)  # Počká 2 sekundy

print('connected')
led1.on()  # LED1 svítí, když je zařízení připojeno
led2.off()  # LED2 nesvítí, když je zařízení připojeno
print('ip = ', wlan.ifconfig()[0])  # Vypíše IP adresu zařízení

s = socket.socket()  # Vytvoří socket
s.bind(socket.getaddrinfo('0.0.0.0', 80)[0][-1])  # Přiřadí socketu IP adresu a port
s.listen(1)  # Nastaví socket do režimu naslouchání s maximálním počtem 1 neakceptovaného spojení
print('listening on', socket.getaddrinfo('0.0.0.0', 80)[0][-1])  # Vypíše, na jaké adrese a portu socket naslouchá

def premapovat_hodnotu(hodnota, min_vlevo, max_vlevo, min_vpravo, max_vpravo):  # Definuje funkci premapovat_hodnotu s pěti parametry
    # Převede hodnotu z jednoho rozsahu na jiný
    rozsah_vlevo = max_vlevo - min_vlevo  # Spočítá rozsah původního intervalu
    rozsah_vpravo = max_vpravo - min_vpravo  # Spočítá rozsah cílového intervalu
    hodnota_v_meritku = float(hodnota - min_vlevo) / float(rozsah_vlevo)  # Spočítá, kde se hodnota nachází v původním intervalu (0 = na začátku, 1 = na konci)
    return min_vpravo + (hodnota_v_meritku * rozsah_vpravo)  # Vrátí hodnotu v cílovém intervalu

while True:  # Neustálý cyklus
    try:  # Pokusí se vykonat následující kód
        cl, adresa = s.accept()  # Přijme příchozí spojení a vrátí nový socket a adresu klienta
        print('client connected from', adresa)  # Vypíše, odkud se klient připojil
        pozadavek = str(cl.recv(1024))  # Přijme data od klienta a převede je na řetězec

        if '/zalit' in pozadavek:  # Pokud je v požadavku '/zalit'
            rele_in.value(1)  # Zapne relé

        elif "/nezalivat" in pozadavek:  # Pokud je v požadavku '/nezalivat'
            rele_in.value(0)  # Vypne relé

        vlhkost_pudy1 = machine.ADC(machine.Pin(26))  # Vytvoří ADC (analogově-digitální převodník) na pinu 26
        senzor = dht.DHT11(machine.Pin(4))  # Vytvoří DHT11 senzor na pinu 4
        senzor.measure()  # Provede měření teploty a vlhkosti vzduchu
        teplota = senzor.temperature()  # Přečte teplotu
        vlhkost_raw = vlhkost_pudy1.read_u16()  # Přečte hodnotu z ADC

        # Kalibrace senzoru
        vlhkost_min = 0  # Minimální hodnota vlhkosti (0%)
        vlhkost_max = 65535  # Maximální hodnota vlhkosti (100%)

        # Převod na procenta
        vlhkost = round(premapovat_hodnotu(vlhkost_raw, vlhkost_min, vlhkost_max, 0, 100), 2)  # Převede hodnotu z ADC na procenta

        # Zde vytváříme HTML dokument, který uvidíme na webovém rozhraním po připojení na IP adressu
        response = """<!DOCTYPE html>
        <html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <title>Document</title>

    <style>
        body{{
            font-family: Arial, Helvetica, sans-serif;
            min-height: 100vh;
            background-image: url("https://t3.ftcdn.net/jpg/03/44/67/38/360_F_344673825_6fU6IORyipkYpfU1mg2vmxtHxDToUO6Q.jpg");
            background-position: center; /* Center the image */
            background-repeat: no-repeat; /* Do not repeat the image */
            background-size: cover;
            color: white;
            margin: 10px;
        }}

        .container{{
            display: flex;
            max-width: 1300px;
            margin: auto;
            width: 100%;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            text-align: center;
        }}

        .teplota{{
            width: 100%;
            border-radius: 20px;
            background: rgba(0, 0, 0, 0.281);
            backdrop-filter: blur(10px);
        }}

        .vlhkost{{
            border-radius: 20px;
            width: 100%;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-evenly;
            gap: 36px;
            padding: 20px 0;
        }}

        .vlhkost div{{
            width: 150px;
            height: 150px;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            border-radius: 50%;
            padding: 36px;
            background: rgba(0, 0, 0, 0.247);
            backdrop-filter: blur(5px);
        }}

        .buttons{{
            width: 100%;
        }}

        button{{
            border-radius: 50%;
            padding: 36px;
            background: rgba(0, 0, 0, 0.247);
            backdrop-filter: blur(5px);
            color: white;
            width: 150px;
            height: 150px;
            font-weight: bold;
            font-size: larger;
            transition: ease .3s;
        }}

        button:hover{{
            transform: scale(1.1);
        }}
    </style>
</head>
<body>
    <h1>Rasbbery zahrádka</h1>
    <div class="container">
        <div class="teplota">
            <h3>Teplota venku</h3>
            <p>Teplota: {} °C</p>
        </div>
        <h3>Vlhkost květináču</h3>
        <div class="vlhkost">
            <div>
                <h3>Jahody převyslí</h3>
                <p>Vlhkost: {} %</p>
            </div>
            <div>
                <h3>Měsíční jahody</h3>
                <p>Vlhkost: 23 %</p>
            </div>
            <div>
                <h3>Máta</h3>
                <p>Vlhkost: 23 %</p>
            </div>
        </div>              
        <div class="buttons">
            <button onclick="window.location.href='/zalit'">Zalít teď</button>
        </div>  
        <div class="buttons">
            <button onclick="window.location.href='/nezalivat'">Stačí</button>
        </div>  
    </div>  
</body>
</html>""".format(senzor, vlhkost) # Zde v tomto pořadí voláme proměné, které se vypíšou v HTML dokurmentu tam, kde jsou prázdné složené
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n') #Pošle HTTP hlavičku
        cl.send(response) # Pošle HTML stránku
        cl.close() # Uzavře spojení s klientem
    except OSError as e: # Pokud dojde k chybě OSError
        cl.close() # Uzavře spojení s klientem
        print("close") # Po uzavření spojení vypíše terminál close
