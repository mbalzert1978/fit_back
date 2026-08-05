---
id: "0038"
title: M6: PortionsToDiary (Recipes -> Diary ueber aufrufer-eigenes Port)
status: blocked
milestone: M6
type: AFK
---

# M6: PortionsToDiary (Recipes -> Diary ueber aufrufer-eigenes Port)

## Parent

Meilenstein [M6](docs/milestones/m6-recipes.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

POST /api/v1/recipes/{id}/portions-to-diary. Recipes definiert ein eigenes schmales DiaryGateway-Protocol (Anti-Corruption-Layer, siehe 'Cross-Context-Kommunikation' in 01-technical-decisions.md) und ruft darueber synchron Diary.AddEntry mit EntrySource.FromRecipe(RecipeId, Portions) auf - kein direkter Import von Diary-Domain/Handler-Code.

## Acceptance criteria

- [ ] 201 mit entryId, unit=Portion|Gram wird korrekt in Gramm umgerechnet
- [ ] 404 recipe-not-found | meal-slot-not-found
- [ ] Der erzeugte Diary-Eintrag traegt EntrySource.FromRecipe mit korrekter RecipeId/Portions (End-to-End-Integrationstest ueber M4.3 + M6.4)
- [ ] Das DiaryGateway-Protocol ist in Recipes' eigenem application/ports/ definiert, die In-Process-Implementierung ruft ausschliesslich Diary's Application-Service auf
- [ ] curl-Beispiel
- [ ] Contract-Test (siehe docs/milestones/02-test-pyramide.md, Form A): Recipes definiert eine implementierungsunabhaengige Test-Suite assert_diary_gateway_contract(gateway) unter contexts/recipes/tests/contracts/, Diary importiert sie und fuehrt sie gegen seinen eigenen In-Process-Adapter aus - ersetzt den bisher als 'End-to-End-Integrationstest ueber M4.3 + M6.4' formulierten Schnittstellenanteil

## Blocked by

- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
