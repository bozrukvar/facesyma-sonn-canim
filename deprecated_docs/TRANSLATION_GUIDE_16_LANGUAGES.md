# Facesyma Personality Discovery Questions - Multi-Language Translation Guide

## Overview
This guide provides translation samples and cultural adaptation guidelines for translating 238 personality discovery questions to 16 languages (238 total = 108 conversation starters + 130 module-specific questions).

## Target Languages (16)
1. **Arabic (ar)** - RTL, formal vs. informal register
2. **Portuguese (pt)** - European/Brazilian variations
3. **Italian (it)** - Formal "Lei" vs. informal "tu"
4. **German (de)** - Formal "Sie" vs. informal "du"
5. **Spanish (es)** - Formal vs. informal "tú/usted"
6. **Japanese (ja)** - Honorifics, politeness levels
7. **Korean (ko)** - Formal vs. informal speech levels
8. **Russian (ru)** - Formal vs. informal "вы/ты"
9. **French (fr)** - Formal "vous" vs. informal "tu"
10. **Chinese (zh)** - Simplified, politeness markers
11. **Hindi (hi)** - Formal vs. informal registers
12. **Bengali (bn)** - Politeness levels, Devanagari script
13. **Indonesian (id)** - Formal Javanese politeness levels
14. **Urdu (ur)** - RTL, formal registers
15. **Vietnamese (vi)** - Politeness markers, no grammatical gender
16. **Polish (pl)** - Formal "Pan/Pani" vs. informal "ty"

## Key Translation Principles

### 1. Tone & Register
- Maintain philosophical depth and introspective nature
- Questions should feel personal yet universal
- Avoid clinical/academic language
- Preserve emotional resonance

### 2. Cultural Appropriateness
- **Formal Languages**: Use formal address forms for initial questions (German Sie, French vous, Spanish usted)
- **Honorifics**: Adapt to language-specific conventions (Japanese keigo, Korean formal-polite)
- **RTL Languages**: Ensure proper text direction (Arabic, Urdu)
- **Gender-specific forms**: Where applicable, use gender-neutral or both forms

### 3. Psychologically Sound Questions
- Maintain open-ended format
- Preserve the existential/reflective quality
- Keep metaphors culturally relevant
- Adapt idioms to local equivalents

### 4. Language-Specific Notes

#### Arabic (ar)
- Use Modern Standard Arabic (MSA) for broad appeal
- Questions use formal "أنت" with respectful tone
- Avoid overly complex grammar
- Right-to-left text direction
- Consider religious/cultural context sensitivity

#### Portuguese (pt)
- Brazilian Portuguese (pt-BR) more common than European (pt-PT)
- Use "você" (informal) or "senhor/a" (formal)
- Philosophical tradition of Lusophone poetry
- Keep poetic resonance

#### Italian (it)
- Use "Lei" (formal) form for professional tone
- Philosophical questions resonate with Italian romanticism
- Maintain lyrical quality of Italian
- "Tu" form works for introspective questions

#### German (de)
- Use "Sie" (formal) for psychological depth
- German philosophical tradition (Heidegger, Kant influence)
- Compound nouns reflect deeper concepts
- Capitalize nouns as per German grammar

#### Spanish (es)
- Use "tú" form (informal but respectful)
- Spanish philosophical tradition
- Poetic resonance in introspective questions
- Castilian or Latin American variants

#### Japanese (ja)
- Use 敬語 (keigo - honorific language) for depth
- Reflective nature suits Japanese introspection
- Question marks: ？for all questions
- Particles (か、の、だろうか) create philosophical tone

#### Korean (ko)
- Use formal-polite style (합니다, 하십니까)
- Korean tradition of deep self-reflection
- Question marker: 까
- Maintains psychological depth

#### Russian (ru)
- Use formal "вы" for introspective questions
- Russian literary tradition supports depth
- Philosophical questions resonate culturally
- Reflexive verbs express self-discovery

#### French (fr)
- Use "tu" for introspective intimacy or "vous" for formal
- French philosophical tradition (Sartre, Camus)
- Maintain existential quality
- Poetic phrasing important

#### Chinese (zh)
- Simplified characters (zh-Hans) for broader access
- Question particle: 吗、呢、没有 at end
- Philosophical depth suits Chinese tradition
- Respect and reflection markers

#### Hindi (hi)
- Use formal "आप" register
- Philosophical concepts resonate in Hindi/Sanskrit
- Devanagari script proper handling
- Respectful inquiry tone

#### Bengali (bn)
- Use formal register with appropriate pronouns
- Philosophical questions align with Bengali literary tradition
- Proper Devanagari transliteration
- Emotional depth preservation

#### Indonesian (id)
- Formal Javanese politeness conventions (Javanese origin)
- Use "Anda" (formal) or "Kami" (inclusive)
- Non-gendered language naturally
- Respectful inquiry tone

#### Urdu (ur)
- Right-to-left script (like Arabic)
- Use formal "آپ" register
- Philosophical concepts from Sufi tradition
- Cultural sensitivity to religious references

#### Vietnamese (vi)
- Use formal "Quý khách/Anh/Chị" as appropriate
- Vietnamese philosophical tradition (Buddhism influence)
- No grammatical tense/gender simplifies translation
- Politeness through context and word choice

#### Polish (pl)
- Use formal "Pan/Pani" register
- Polish philosophical tradition
- Deep introspective questions resonate culturally
- Grammatical gender in nouns maintained

---

## Sample Translations Structure

For each language, we provide:
1. **5-7 samples from conversation_starters.json** (covering different categories)
2. **5-7 samples from module_specific_questions.json** (covering different modules)
3. **Pattern Guidelines** for translating remaining questions
4. **Language-Specific Considerations**

---

## Implementation Notes

### For Translators
1. Start with provided samples to establish tone and style
2. Follow patterns for similar questions
3. Test questions for psychological soundness
4. Consider cultural idioms and metaphors
5. Preserve open-ended, reflective nature

### For Integration
1. Add translated versions to existing JSON structure
2. Add language codes to metadata "languages" array
3. Update "questions_[lang]" keys for each category/module
4. Test RTL rendering for Arabic and Urdu
5. Validate character encoding (UTF-8)

### Quality Assurance
- [ ] Verify all 108 conversation starters translated
- [ ] Verify all 130 module-specific questions translated
- [ ] Check RTL languages render correctly
- [ ] Validate all special characters/diacritics
- [ ] Test in RAG system with language parameter
- [ ] Native speaker review recommended

---

## File Organization

All translations provided as JSON snippets in separate files:
- `translations_ar.json` - Arabic
- `translations_pt.json` - Portuguese
- `translations_it.json` - Italian
- `translations_de.json` - German
- `translations_es.json` - Spanish
- `translations_ja.json` - Japanese
- `translations_ko.json` - Korean
- `translations_ru.json` - Russian
- `translations_fr.json` - French
- `translations_zh.json` - Chinese (Simplified)
- `translations_hi.json` - Hindi
- `translations_bn.json` - Bengali
- `translations_id.json` - Indonesian
- `translations_ur.json` - Urdu
- `translations_vi.json` - Vietnamese
- `translations_pl.json` - Polish

---

## Next Steps

1. Review sample translations in provided JSON files
2. Adapt patterns for complete translation set
3. Validate with native speakers if possible
4. Merge into main conversation_starters.json and module_specific_questions.json
5. Test in RAG system with language switching
