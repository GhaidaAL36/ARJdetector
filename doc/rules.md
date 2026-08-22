# The Arabic behind ARJ Detector

Part I is the grammar: what each rule claims about Arabic, and why. Part II is
the application: how each of those claims becomes a test in the code, and where
the grammar runs out and a stored list takes over.


---

# Part I — The grammar

## 0. Why عرنجية needs a tool of its own

Both patterns this detector looks for are **completely grammatical Arabic**. Run
them past any نحو checker and nothing fires, because nothing is wrong:

- «بشكل كبير» — بـ is حرف جر, شكل is اسم مجرور, كبير is نعت مجرور. Flawless.
- «تم إغلاق الباب» — تمّ is فعل ماضٍ, إغلاق is فاعل مرفوع, الباب is مضاف إليه.
  Flawless.

What is wrong is *structural*: the sentence is assembled the way an English
sentence is assembled, using Arabic words. Spell-checkers work on words and
grammar-checkers work on إعراب, so neither can see it. The judgment being made
here is stylistic — "Arabic has a shorter, native way to say this" — but it has
to be reached from **structural evidence only**, because that is the only kind of
evidence a program can verify.

That constraint shapes every rule below. Each one is built as: *a native Arabic
construction exists → the text used an imported construction instead → and here
is a syntactic fact that proves which of the two this is.*

---

## 1. Rule one — «بشكل» + وصف

### 1.1 How Arabic expresses manner natively

Arabic marks manner **on a word**, not with a prepositional phrase. It has at
least four native devices:

| device | example |
|---|---|
| الحال | عاد الجنودُ **منتصرين** |
| المفعول المطلق المبيّن للنوع | نجح **نجاحاً باهراً** |
| النائب عن المفعول المطلق | ضربه **ضربَ الأمير** |
| الظرف/المصدر المنصوب (adverbial accusative) | تمّ التوقيع **رسمياً**، يُنشر **يومياً** |

The common thread: the manner rides on a single inflected word, usually carrying
النصب. Arabic has a *case ending* available for the job, so it uses it.

### 1.2 What English does, and what gets copied

English has no adverbial case. It marks manner with a suffix (`-ly`) or, when
that is unavailable or awkward, with a prepositional phrase: *in a formal way*,
*in a significant manner*, *on a large scale*.

Translating phrase-for-phrase gives:

> in a formal way → **بشكل رسمي**
> significantly → **بشكل ملحوظ**
> directly → **بشكل مباشر**

The output is grammatical, and that is exactly the problem. A three-word
prepositional phrase has replaced a one-word adverb — `رسمياً`, `بوضوح`,
`مباشرةً` — and in translated prose it appears at a rate no native register
matches.

**The claim of rule one:** where بشكل introduces a description of *how*
something happened, a native adverbial exists and is shorter.

### 1.3 When بشكل is perfectly fine

Three uses that are not عرنجية at all:

**(أ) الشكل بمعناه الحقيقي — the literal shape.** «بشكل دائري»، «بشكل هلال»،
«بشكل سلسلة بشرية». Here شكل means *form*, and the phrase describes geometry,
not manner. Nothing to rewrite.

**(ب) الإضافة.** «بشكل الهرم» — شكل is مضاف and الهرم is مضاف إليه: "in the
shape of the pyramid". A completely different construction that happens to start
with the same two words.

**(ج) التعبيرات المسكوكة.** «بشكل ما»، «بشكل أو بآخر»، «بشكل من الأشكال»،
«بشكل لا يصدق». Fixed expressions; the word after بشكل is not a descriptor at
all.

### 1.4 The grammatical test — التنكير والتعريف

This is the sharpest tool in rule one, and it is pure syntax, no word list.

**النعت يتبع المنعوت في التعريف والتنكير.** An adjective agrees with its noun in
definiteness.

In the adverbial construction, شكل is **نكرة** — fully vocalized it carries
tanwin: «بشكلٍ كبيرٍ». Therefore any adjective describing it must also be نكرة.
It is impossible to say «بشكلٍ الكبير».

So if the word after بشكل is **معرّف بأل**, it cannot be a نعت. Grammar leaves
only one option: it is a **مضاف إليه**, and the phrase is the literal
"shape-of-X" genitive.

> «بشكل كبير» → كبير نكرة → نعت → the adverbial reading → **flag**
> «بشكل الهرم» → الهرم معرفة → مضاف إليه → the literal reading → **pass**

One syntactic fact separates the two readings with no semantics involved. It is
also what makes it safe to accept `noun` as a target POS (§1.6): the definite
case — the one that would produce false positives — is already gone.

### 1.5 Where grammar runs out — المعنى

«بشكل دائري» and «بشكل رسمي» are **syntactically identical**: بـ + شكل نكرة +
صفة نسبة نكرة. Same structure, same measure, same definiteness. The only
difference is whether شكل is meant literally, and that is **word sense**, not
morphology.

Your own testing confirms no available field encodes it:

- Arramooz's `category`: دائرة is `جامد` — and so is يوم.
- Arramooz's `wordtype`: `جيد` and `عام` are `جامد` exactly like `هلال`;
  `مستطيل` is `اسم فاعل` exactly like `مباشر`.

There is one place the signal does survive — **fully vocalized text**. «بشكلِ
هلالٍ» has no tanwin on شكل (it is مضاف), while «بشكلٍ نهائيّ» does. But
`preprocess` strips diacritics, and real input rarely carries them.

So this gap, and only this gap, is filled by a stored list: 22 shape lemmas,
keyed by **lemma** so that هرمي/هرمية/الهرم all reduce to هرم, and grown only
from words actually observed in text.

### 1.6 Why "the target must be an adjective" was abandoned

Linguistically the target *is* a نعت, so `pos == "adj"` looks like the obvious
test. It was tried and it leaked, measured on 24 real adverbial uses:

- `مباشر` and `عام` come back `noun`;
- `يومي` comes back `noun`, lemmatised to `يوم`;
- `حسن` comes back `noun_prop`, because it is also a personal name.

6 of 24 real cases were missed. The fix inverts the test: instead of requiring
the tag CAMeL reports *unreliably*, exclude the tags it reports **reliably** —
`prep`, `conj`, `part_neg`, `pron_rel`. Those are exactly the fixed expressions
of §1.3(ج), so «بشكل ما»، «بشكل من الأشكال»، «بشكل لا يصدق» و«بشكل أو بآخر» all
fall out for free.

### 1.7 One more structural fact — الاعتراض

Arabic allows a parenthetical between the phrase and its adjective:

> «بشكل - ولله الحمد - كبير»

The described word is كبير, not ولله. The rule therefore does not assume the
target is adjacent; it steps over a bracketed aside as a unit.

---

## 2. Rule two — «تمّ» + مصدر

### 2.1 Arabic's passive is one word: المبني للمجهول

Arabic builds the passive by **internal vowel change**, not with a helper verb:

| معلوم | مجهول |
|---|---|
| أَغلَقَ البابَ | **أُغلِقَ** البابُ |
| يُغلِقُ البابَ | **يُغلَقُ** البابُ |
| كَتَبَ المقالَ | **كُتِبَ** المقالُ |

The pattern for الماضي is ضمّ الأول وكسر ما قبل الآخر; for المضارع, ضمّ الأول
وفتح ما قبل الآخر. The **مفعول به** is promoted to **نائب فاعل** and takes
الرفع.

There is no auxiliary verb in this. Arabic simply does not need one.

### 2.2 What English does, and what gets copied

The English passive is *periphrastic* — it needs a helper: *was closed*, *was
carried out*, *was completed*. Translating that shape into Arabic reaches for a
helper Arabic has available: تمّ.

> the door was closed → **تم إغلاق الباب**
> the agreement was signed → **تم توقيع الاتفاقية**

تمّ is a real verb with a real meaning: تمَّ الشيءُ = *it became complete*. What
is imported is not the word but its **role** — pressing it into service as a
passive auxiliary, which Arabic never required.

**The claim of rule two:** where تمّ + مصدر stands in for a passive, the native
one-word passive exists — «أُغلق الباب».

### 2.3 The condition that makes the claim true — التعدّي

This is the heart of the rule, and it is why transitivity is not a heuristic but
a **precondition**.

The passive rewrite works by promoting the مفعول به to نائب فاعل. **Only a فعل
متعدٍّ has a مفعول به.** So:

> **تم إغلاق الباب** — أغلق متعدٍّ، الباب مفعول به → أُغلِقَ البابُ ✔
> the rewrite exists, so the original is a substitute for it → **flag**

> **تم وصول الوفد** — وصل لازم، لا مفعول به → there is nothing to promote ✘
> no passive rewrite exists, so تمّ is not standing in for one. It is doing its
> own job: stating that the arrival occurred → **pass**

(An intransitive verb can technically take a نائب فاعل from a جار ومجرور or ظرف
— «سِيرَ في الطريق» — but that is a marked classical construction, not a
translation of what the sentence means.)

So the tool's question is never "does this look translated?" It is: **does a
native passive rewrite exist for this sentence?** Transitivity is how you find
out, and that is a fact you can look up.

### 2.4 The second condition — it must be a مصدر

تمّ followed by an ordinary noun is plain Arabic, not a passive at all:

> «تم الأمرُ بسرعة» — تمّ with a noun subject. "The matter was completed."

Only a **مصدر** carries the verbal meaning that a passive verb would replace.

Here is the linguistic reason this is hard, and it is worth stating precisely
because it explains where every remaining false positive comes from:

**أوزان المصادر في الأفعال المزيدة قياسية، وفي الثلاثي المجرد سماعية.**

For the augmented measures (II–X), the masdar has a *predictable* pattern —
تفعيل، إفعال، استفعال، افتعال، مفاعلة، تفعّل، تفاعل، انفعال. `classify_measure`
separates these cleanly (7/7 in your testing).

For the bare triliteral (measure I), the masdar is **سماعي** — فَعْل، فَعَل،
فُعُول — and those are exactly the shapes of ordinary nouns:

| مصدر | اسم عادي | same shape? |
|---|---|---|
| فَتْح | رَجُل | yes |
| رَفْض | خَبَر | yes |
| نَقْل | كِتاب | yes |

There is no morphological difference to find. Nor does derivation help:
الكتاب→كتب، الرجل→رجل، الخبر→خبر all "derive" perfectly well, because Arabic
roots are shared across the whole lexicon. **A successful derivation is not
evidence of masdar-hood.**

Separating فتح (an opening) from كتاب (a book) is word-sense disambiguation, and
no field in CAMeL or Arramooz encodes it — `pos`, `catib6`, `ud` and `rat` are
identical for both, and `gloss` differs only in English wording.

This is why the masdar check is used as a **negative filter only**: a `True` is
weak (Arramooz records that a masdar *sense exists*, not which sense is meant, so
أمر comes back True even as a plain noun), while a `False` is strong. And it is
why the residue is handled by four stored words, not by a noun lexicon.

### 2.5 The exception — العطف بالواو

> «تم التدقيق والمراجعة»
> «تم مراجعة التقارير، وتدقيق الحسابات»

These are **مصادر معطوفة** — a list of things that happened, coordinated by و.
The sentence is enumerating, not Arabizing one passive, and a passive rewrite
would have to distribute across the whole list. Rule two leaves them alone.

Four grammatical facts shape how the check is written:

1. **الواو حرف عطف** joining a معطوف to a معطوف عليه — so the second masdar is
   parallel to the first, and both are governed by تمّ.
2. **The و is rarely adjacent.** A masdar normally carries its object first
   («مراجعة التقارير»), so the coordination appears several tokens later. In
   every real chain example you collected, the و sat at token 4.
3. **الفاصلة ليست نهاية.** A comma separates chain members; it does not end the
   list. A **verb**, on the other hand, opens a new جملة — «تم إغلاق الباب
   وذهب الرجل» is two sentences and the first masdar is judged on its own.
4. **واو العطف ≠ واو أصلية.** In وصول، وقوع، وزير، ولادة the و is a **حرف
   أصلي** — part of the root, not a conjunction. Deciding this from spelling
   would be wrong every time.

And one more: a chain member is a **bare noun**. «وبشكل» is و + بـ + شكل — a
جار ومجرور opening its own phrase, not something coordinated with the masdar.

(**الفاء is deliberately out of scope.** The rule as written speaks of و-linked
lists only.)

### 2.6 The morphological chain the rule needs

To get from a masdar in running text to a transitivity verdict, the code has to
walk the same path a صرف student would:

```
المصدر  →  الوزن  →  الجذر  →  الفعل المجرد/المزيد  →  متعدٍّ أم لازم؟
إغلاق   →  إفعال  →  غ ل ق  →  أغلق                →  متعدٍّ  →  flag
```

Each step needs a piece of Arabic morphology to be handled correctly:

**الجذر والإعلال.** Roots are three radicals, but a **فعل معتل** hides one:
الأجوف (قال، قام) loses its middle radical in some forms. The analyzer marks the
missing radical as `#`, so the code must recover it — either by reading the
resolved letter out of the pattern (a hollow root spells it literally: `تَ1ْيِي3`
for تقييم vs `تَ1ْوِي3` for تطوير) or by trying **و / ي / ء** in turn.

**الهمزة.** Written six ways (ء أ إ آ ئ ؤ) depending on its seat, but one
radical. Comparison must normalise them or استئناف fails to match its own root.

**الأوزان I–X.** Distinguishing أفعل (IV) from افتعل (VIII) from استفعل (X) is
what makes the root lookup land on the right verb.

**إبدال تاء الافتعال.** In وزن افتعل, the ت assimilates to its neighbour:

| after | ت becomes | example |
|---|---|---|
| ص ض ط ظ | **ط** | اضطراب، اصطبار |
| ز د ذ | **د** | ازدحام |
| (sometimes fully) | merges | ادّخار |

Without this, اضطراب never reads as افتعال and gets matched against a تفاعل verb.

**التضعيف والشدّة.** الشدّة is what separates فعّل (II) from فعَل (I). And a
**فعل مضعّف** contracts: حَلَّ is spelled حل — two letters — so a two-letter verb
with shadda is still measure I, not something malformed.

**أل التعريف.** «تم الاتفاق» is at least as common as «تم اتفاق», and the ال
rides along inside the pattern, hiding the measure's opening marks. It has to be
stripped — but **from the pattern, never from the spelling**: radicals appear in
patterns as digits, so a literal ال there can only be the determiner, whereas
التزام and التقاء open with ا and ل that are **root material**.

### 2.7 Where the chain runs out

**استلام.** وزن افتعال with س as its first radical is spelled identically to
استفعال **and shares the same root**, so neither shape nor root separates
استلم from استسلم. No morphological signal exists. Arramooz holds only 11 such
verbs in total — a bounded set — so a single stored entry closes it.

**تم بناء البرج.** Whether this is عرنجية depends on the surrounding discourse:
in a long text about a project finishing after years, تمّ genuinely means "was
completed" and the sentence is fine; in a short news line it is the Arabized
passive. The detector reads one sentence at a time and cannot make that call —
a documented limitation, not a bug.

---

# Part II — How the grammar becomes code

## 3. Rule one, condition by condition

| # | Arabic principle | The test | Implemented in |
|---|---|---|---|
| 1 | The construction opens with بـ + شكل, and may carry و/ف | `word.endswith("بشكل")` | `find_bshakl_matches` |
| 2 | A parenthetical may separate the phrase from its نعت | skip a matched delimiter pair as one unit (≤ 8 tokens inside, ≤ 3 skips) | `next_target_index` + `_closing_index` |
| 3 | Some shape names are multi-word (شبه منحرف) | compare the next *n* tokens to a stored phrase | `is_phrase_whitelisted` |
| 4 | شكل may be meant literally — **word sense, no field encodes it** | lemma against 22 stored shape words | `is_whitelisted_lemma` |
| 5 | «بشكل واحد» is the literal "in one form" | lemma against `force_excluded_lemmas` | `is_force_excluded` |
| 6 | **النعت يتبع المنعوت في التنكير** — a definite target cannot be a نعت, so it is a مضاف إليه | `prc0 == "Al_det"` → reject | `describes_shakl` |
| 7 | The target must be a descriptor, but `adj` is unreliably tagged | accept `adj`/`noun`/`noun_prop`; the fixed expressions fall out as `prep`/`conj`/`part_neg`/`pron_rel` | `describes_shakl` |

Order matters and is deliberate: cheap and decisive tests first, and the two
list-based tests (4, 5) run **before** the grammatical verdict (6, 7), so a
literal shape never reaches the syntactic reasoning at all.

## 4. Rule two, condition by condition

| # | Arabic principle | The test | Implemented in |
|---|---|---|---|
| 1 | تمّ must be **the verb** تمّ — not any word ending in تم (خاتم، حاتم، مأتم) | `lex == "تم" and pos == "verb"` | `is_tam_trigger` |
| 2 | An adverbial may sit between تمّ and its مصدر («يتمّ حالياً إجراء الصيانة») | walk forward to the first `noun`, stopping at a verb or sentence end | `masdar_target_index` |
| 3 | **العطف بالواو** — a list of مصادر is not one passive | scan forward for a standalone `و`, or a `noun` whose `prc2` is a و-proclitic and whose `prc1` is empty; stop at a verb or `. ! ? ؟ ۔`, but **not** at a comma | `is_in_waw_chain` |
| 4 | تمّ + اسم عادي is ordinary Arabic | Arramooz `nouns` table, as a **negative filter only** (`None` must not suppress) | `is_masdar` + `force_not_masdar` |
| 5 | Some masdars are intransitive in their own sense even where the verb is not (عدول عن) | stored list, keyed by **masdar** — عدول and تعديل both derive to عدل | `is_force_intransitive_masdar` |
| 6 | المصدر → الوزن → الجذر → الفعل | measure classification, root recovery, shape matching | `derive_base_verb` and `morphology.py` |
| 7 | A flag must not rest on a guessed verb | only trusted derivation statuses proceed | `is_trusted_derivation` |
| 8 | **التعدّي** — only a متعدٍّ verb has a مفعول به to promote to نائب فاعل | Arramooz `verbs.transitive` | `is_transitive_verb` |

Two orderings encode grammar rather than performance:

- **The و-chain check runs before derivation.** A chain never flags, so deriving
  first would be discarded work — and the chain is a fact about syntax that does
  not depend on the verb at all.
- **The masdar override runs before derivation**, because derivation destroys the
  distinction it needs: عدول and تعديل both arrive at عدل, so a verb-keyed
  override could not tell «تم العدول عن القرار» from «تم تعديل النظام».

## 5. Which Arabic fact each data field carries

The rules never read spelling where a morphological field exists. This is the
map:

| Arabic fact | field | why not spelling |
|---|---|---|
| هل الكلمة معرفة بأل؟ | `prc0` = `Al_det` | the article is attached, not a separate token |
| هل تحمل حرف جر؟ | `prc1` = `bi_prep` | «وبشكل» is one token holding و + بـ + شكل |
| هل الواو حرف عطف أم أصلية؟ | `prc2` ∈ `wa_part / wa_conj / wa_sub` | وصول، وقوع، وزير all *start* with و; only the analysis knows it is root material. CAMeL splits the conjunction across three values depending on its reading — matching only one misses half the real chains |
| ما نوع الكلمة؟ | `pos` | — |
| ما جذرها الأصلي بعد التصريف؟ | `lex` (lemma) | one whitelist entry (هرم) then covers هرمي، هرمية، الهرم |
| ما وزنها؟ | `pattern`, raw and still vocalized | the diacritics are the measure's marks; the dediacritized copy cannot classify |
| ما جذرها؟ | `root`, with `#` for a hidden weak radical | — |
| متعدٍّ أم لازم؟ | Arramooz `verbs.transitive` | not derivable from the pattern: patterns overlap ~100% between transitive and intransitive masdars across all 7 measures tested |

## 6. Every stored list, and the exact linguistic gap it fills

The project's rule is that a hand-maintained list is acceptable **only** where an
algorithmic mechanism has a known, finite gap — never as the primary mechanism.
Each list, and the gap:

| list | size | the gap it fills |
|---|---|---|
| `whitelisted_lemmas` | 22 | **word sense.** «بشكل دائري» and «بشكل رسمي» are syntactically identical; no field in CAMeL or Arramooz separates them, and the one signal that would (tanwin on شكل) is stripped by dediacritization |
| `whitelisted_phrases` | 1 | a shape name that is only identifiable whole — شبه alone is not a shape word |
| `force_excluded_lemmas` | 1 | «بشكل واحد» = "in one form", a literal reading with no shape word in it |
| `force_not_masdar` | 4 | the **measure-I** masdar/noun overlap — سماعي masdar shapes are identical to ordinary noun shapes, and Arramooz reports that a masdar sense *exists* rather than which sense is used |
| `force_intransitive_masdars` | 20 | Arramooz's transitivity is **classical and broad**; these masdars' own senses are intransitive in modern usage. Keyed by masdar because unvocalized verbs collide across measures (عدول/تعديل → عدل) |
| `force_derived_verbs` | 1 | افتعال with a س first radical is spelled exactly like استفعال and shares its root — 11 such verbs exist in total, and only استلام is in real use |
| `force_intransitive_verbs` | 0 | kept for a verb that is intransitive in **every** sense; all 19 original entries moved to the masdar list after the توقيع collision |

Every one of these is bounded and justified by a specific failure of an
algorithmic mechanism. The lists the project explicitly refuses to build are the
open-ended ones: a full noun lexicon for the measure-I residue (الوقت، العمل،
الرجل، الكتاب، اللقاء، الخبر), and a general shape vocabulary.

## 7. Worked sentences — the grammar and the code side by side

**«الجو جميل بشكل رائع اليوم»** → flagged

رائع نكرة → it can only be نعت for شكل → the adverbial reading. Not a shape
word, not a fixed expression. Native rewrite: «الجو جميل اليوم» or «رائعُ
الجمال».
*Code:* `endswith` ✓ → target = رائع → not whitelisted → `prc0 = "0"`, `pos =
adj` → **flag** «بشكل رائع».

**«بشكل الهرم»** → clean

الهرم معرفة → cannot be a نعت for نكرة → it is مضاف إليه → the literal
"shape-of" genitive.
*Code:* stopped by the lemma whitelist (هرم) first; `describes_shakl` would have
rejected it on `prc0 == "Al_det"` regardless. Two independent defences.

**«تم إغلاق الباب»** → flagged

إغلاق is وزن إفعال of أغلق, a فعل متعدٍّ whose مفعول به is الباب. The passive
rewrite exists: **أُغلِقَ البابُ**.
*Code:* trigger on lex+pos → target إغلاق (noun) → no و-chain → masdar not denied
→ derive إغلاق → إفعال → غ.ل.ق → أغلق (`unique_match`) → transitive → **flag**.

**«تم مراجعة التقارير، وتدقيق الحسابات»** → clean

مصدران معطوفان — an enumeration. The comma is internal to the list, and the و on
وتدقيق is حرف عطف, not a root letter.
*Code:* the forward scan reaches وتدقيق (`prc2 = wa_part`, `pos = noun`, `prc1 =
0`) → chain → skip, without ever deriving a verb.

**«اشترى خاتم الذهب»** → clean

خاتم is an اسم that merely *ends* in تم; its lemma is خاتم and its POS is noun.
*Code:* `is_tam_trigger` matches on lex + pos, so it never fires. A spelling test
(`endswith("تم")`) would have produced a false positive here — which is precisely
why rule two does not use the shape of rule one.

**«تم وصول الوفد»** → clean

وصل لازم — there is no مفعول به to promote, so no passive rewrite exists and تمّ
is not standing in for one.
*Code:* وصول is in `force_intransitive_masdars`, so it stops before derivation;
had it not been, Arramooz's classical entry would have called وصل transitive,
which is the exact gap that list exists to close.

---

## 8. Glossary

| term | meaning | where it shows up in the code |
|---|---|---|
| **عرنجية** | Arabic whose structure is imported from English | the whole project |
| **المصدر** | verbal noun (إغلاق، مراجعة، فتح) | `is_masdar`, `masdar_target_index` |
| **المبني للمجهول** | the internal-vowel passive (أُغلِقَ) | the rewrite rule two proposes |
| **نائب الفاعل** | the promoted object in a passive | why transitivity is required |
| **متعدٍّ / لازم** | transitive / intransitive | `is_transitive_verb` |
| **الوزن (I–X)** | verb measure — فعل، فعّل، فاعل، أفعل، تفعّل، تفاعل، انفعل، افتعل، استفعل | `classify_measure` |
| **الجذر** | the root radicals | `generate_root_candidates` |
| **المعتل / الأجوف** | a root with a weak radical (و/ي/ء) | `hollow_weak_letter_from_pattern`, `WEAK_LETTERS` |
| **إبدال تاء الافتعال** | the ت of افتعل becoming ط or د | `VIII_INFIX_BY_RADICAL` |
| **التضعيف / الشدّة** | doubling — separates فعّل from فعل | `SHADDA`, measure I and II tests |
| **النعت والمنعوت** | adjective and its noun, agreeing in definiteness | `describes_shakl` |
| **الإضافة** | the genitive construction | the `Al_det` rejection |
| **التنكير والتعريف** | indefinite vs definite | `prc0` |
| **حرف العطف** | conjunction — و here | `WAW_PROCLITICS` |
| **الحال / المفعول المطلق** | the native manner constructions | what rule one suggests instead |
| **النسبة** | the ـيّ adjective (رسمي، دائري) | appears on both sides — not a discriminator |
| **الاعتراض** | a parenthetical insertion | `ASIDE_DELIMITERS` |
