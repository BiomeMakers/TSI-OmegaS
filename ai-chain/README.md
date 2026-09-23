# Off-balance-sheet guarantees in the AI supply chain

Companion material to *Chips and Megawatts: a network measurement of the AI supply chain*
(SSRN 7307362, 19 August 2026), which measured that structural weight in the chain had moved from
the buyers of compute towards their suppliers and towards power, using price data alone.

This folder goes to a different source, the filings themselves, and reports what each company
discloses about the guarantees that back the debt of data centres it does not own.

## The note

`NOTA_GARANTIAS.pdf` (four pages). Main finding: the same instrument is disclosed three different
ways, so a reader of the quarterly statements cannot add them.

- Alphabet: maximum potential payment, in its quarterly accounts. $16.9bn in December 2025,
  $28.4bn in March 2026, $43.8bn in June 2026.
- Broadcom: maximum liability and the formula behind it, in its quarterly accounts. $29bn.
- NVIDIA: aggregate cap of $105bn, in the Form 8-K filed on the day of the deal. Its quarterly
  accounts report only a fair value, described as not significant.
- Meta: leases signed but not yet commenced, from $7.1bn (December 2023) to $103.8bn
  (December 2025), plus residual value guarantees of $28bn and a further $13bn.

## Files

| file | content |
|---|---|
| `NOTA_GARANTIAS.pdf`, `.md` | the note, with every figure linked to its source filing |
| `extraer_garantias_v2.py` | extractor: EDGAR full-text search, sentence-level extraction |
| `garantias_v2_frases.csv` | 1,187 sentences with amounts, context and source link |
| `garantias_v2_aristas.csv` | guarantor and counterparty pairs, draft |
| `meta_arrendamientos.csv`, `alphabet_respaldos.csv` | the two series plotted in the note |
| `precios_y_contratos.png`, `series_declaradas.png`, `promesas.png` | figures |

## Reproducing the extraction

```bash
python3 extraer_garantias_v2.py --email your.address@example.com
```

The SEC requires a contact address in the request header for automated access. The run covers
13 companies, 21 search terms and forms 10-K, 10-Q and 8-K filed from January 2024 onwards, and
writes the two CSV files above.

## Two limitations, stated

The extractor reads the main document of each filing and not its exhibits, which is why the NVIDIA
figure had to be recovered from the body of the 8-K separately. And amounts are taken from the
sentence in which they appear, so any figure quoted elsewhere must be verified against the source
document first, as was done for every figure in the note.

## Citation

Acedo, A. (2026). *Chips and Megawatts: a network measurement of the AI supply chain.*
SSRN 7307362. https://ssrn.com/abstract=7307362
