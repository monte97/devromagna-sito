---
title: "CQRS + ES + GDPR = Broadway Sensitive Serialize"
date: 2022-09-22T19:00:00+02:00
city: "Faenza"
host: "Abilio S.p.A."
abstract: "CQRS+ES (Command Query Responsibility Segregation + Event Sourcing) è un pattern che permette la segregazione delle operazioni di lettura da quelle di scrittura, attraverso l'emissione e l'ascolto di eventi al fine di gestire lo stato ultimo di un Aggregato. Gli eventi sono per loro natura immutabili; ciò che è successo in passato, non cambia. Come si può sposare questo principio con la GDPR?"
meetup_url: "https://www.meetup.com/devromagna/events/286896133/"
speakers:
  - "Matteo Galacci"
address: "Via Galileo Galilei, 6"
map_url: "https://www.google.com/maps/search/?api=1&query=44.296080,11.860612"
end: 2022-09-22T21:00:00+02:00
---

CQRS+ES (Command Query Responsibility Segregation + Event Sourcing) è un pattern che permette la segregazione delle operazioni di lettura da quelle di scrittura, attraverso l'emissione e l'ascolto di eventi al fine di gestire lo stato ultimo di un Aggregato. Gli eventi sono per loro natura immutabili; ciò che è successo in passato, non cambia. Come si può sposare questo principio con la GDPR?

Nello specifico l'art. 17, il diritto all'oblio, dice che l'interessato ha il diritto di ottenere dal titolare del trattamento la cancellazione dei dati personali che lo riguardano senza ingiustificato ritardo e il titolare del trattamento ha l'obbligo di cancellare senza ingiustificato ritardo i dati personali. Ma se un evento non può essere modificato, né tantomeno cancellato, come possiamo garantire questo diritto?

L'idea dietro a Broadway Sensitive Serializer è quella di rendere compliant un sistema CQRS+ES, nello specifico implementato attraverso la libreria Broadway, con il regolamento generale sulla protezione dei dati (GDPR), in particolare con il diritto all'oblio. Il principio base è di creare fin dall'inizio eventi criptati (interamente o parzialmente) attraverso una chiave specifica per ogni Aggregato. Quando un utente chiederà di essere cancellato, verrà cestinata la chiave, rendendo i dati sensibili contenuti nell'evento non più leggibili, ma gli eventi, e quindi tutto lo storico, saranno disponibili e consistenti.

L'idea alla base di questo progetto non riguarda la sicurezza generale o la fuga di dati. L'idea è piuttosto quella di rendere un sistema CQRS+ES conforme al diritto dell'utente di chiedere in qualsiasi momento di essere dimenticato, mantenendo il sistema basato su eventi, consistente. Può essere quindi usata anche in un contesto diverso dalla legge GDPR, dal momento che in pratica non fa altro che decorare il serializzatore di Broadway, dandogli la capacità di criptare e decriptare il payload degli eventi sulla base di alcune strategie.

