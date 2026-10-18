# Second brain installeren

Een second brain onthoudt alles wat je met Claude Code doet en geeft het terug wanneer het helpt, in elk project,
op je Mac en in cloudsessies.

## Zo installeer je het

Open Claude Code en plak deze prompt:

```
Installeer mijn second brain. Voer uit:
curl -fsSL https://raw.githubusercontent.com/madebyvalentine/second-brain-install/main/install.sh -o ~/brain-install.sh && bash ~/brain-install.sh start
Volg daarna precies wat het script zegt. Zegt het "NEED name" of "NEED email", vraag mij dat dan en voer het opnieuw
uit met --name "..." of --email .... Zegt het "Volgende stap: ...", voer die stap uit. Bij "NEED api_key" vraag je
mij om mijn Anthropic API-key en geef je die door via stdin aan: bash ~/brain-install.sh token
Vertel mij alleen de regels die het script print, verder niets.
```

Daarna wacht je. Valentine krijgt je aanvraag te zien en keurt hem goed. Zodra je brein klaar is, zegt Claude
het, en vanaf je volgende sessie werkt het.

Nu alleen voor de Mac. Windows komt binnenkort.

## Wat er op je computer verandert

- `~/.second-brain/`: het adres van je brein, een kleine client en, als je Mac er geen heeft, een eigen Python.
- In de Claude Code-instellingen (`~/.claude/settings.json`) komen vijf hooks bij. Je eigen instellingen blijven
  staan; een kopie van hoe ze waren staat in `settings.json.before-brain`.
- De tools van je brein (`second-brain`) in elke sessie, en een korte uitleg voor Claude in `~/.claude/CLAUDE.md`.
- De sleutel van je brein staat in de sleutelhanger van je Mac, niet in een bestand.
