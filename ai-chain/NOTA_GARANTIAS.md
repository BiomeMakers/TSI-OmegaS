# Three Ways to Disclose the Same Guarantee

**What the filings of the AI supply chain say about off-balance-sheet exposure, and why it cannot be added up**

Alberto Acedo, PhD — Biome Makers Inc. — 23 September 2026

## Summary

In August I measured the AI supply chain as a correlation network over ten years, using nothing but
prices [1]. The result was a shift: structural weight moved away from the companies buying compute and
towards their suppliers, and above all towards power. Hyperscalers and software fell from 23.5% to 17.2%
of the block's weight; electrical equipment makers rose from 8.4% to 14.8%. The measurement said where the
load had gone. It could not say through what.

On 20 September the Financial Times reported the contracts that move it: up to $300bn of guarantees
issued in under a year to back the debt of data centres the tech companies do not own [2]. That is the
mechanism my measurement could not see, and it points the same way: two suppliers, Nvidia and Broadcom,
now guarantee the obligations of their own customers.

Two observations of the same shift, from independent sources: one from prices, one from contracts. This
note adds a third, made here: an extraction from the filings themselves, 1,187 sentences across 279
filings of 13 companies, to see what each company actually discloses and in which document. The finding
is not a number. It is that the same instrument is disclosed in three different ways, so that a reader of
the quarterly statements cannot add them.

## A guarantee moves the debt off the balance sheet without moving the risk

A company wants to use a data centre without carrying its debt. A third party builds and finances it and
leases it to the company. To make the lenders comfortable, the company promises a floor: if the tenant
fails and the asset is worth less than an agreed threshold, it covers the shortfall. It does not pay the
lease or the debt; it covers the gap. Under US accounting rules the liability is only recorded when
payment becomes probable, which is why most filings state that it is not probable and record nothing.

## The same guarantee is published as a ceiling, as a formula, and as a fair value near zero

Alphabet discloses the maximum potential amount of future payments in its quarterly statements. As of
December 2025: $5.7bn in financial guarantees and $16.9bn in credit derivatives. As of March 2026: $9.0bn
and $28.4bn. As of June 2026: $7.6bn and $43.8bn [3][4][5]. The credit derivative figure multiplies by 2.6
in six months, and the filing states that the notional amounts represent the maximum potential exposure in
specified default scenarios.

Broadcom discloses the maximum liability and the formula. Its quarterly filing of 10 September 2026 states
that the maximum potential liability under the backstop, upon deployment of all AI racks, on an
undiscounted basis, was approximately $29bn, and that in the event of a tenant default its liability equals
the difference between 85% of the outstanding lease amounts and the value of the racks recovered on sale.
It adds that no amounts have been paid and the fair value of the backstop is not material [6].

Nvidia discloses the amount in the event filing, and only the fair value in the quarterly statements. The
Form 8-K of 17 August 2026 states that Nvidia entered into residual value guaranties with SB Energy for
approximately 4.25 GW of IT load at the Portsmouth site, that it may provide credit support for a further
3.8 GW at its sole discretion, and that its aggregate payment obligation is cumulatively capped at $105bn
[7]. The quarterly filing of 26 August 2026 says only that such guarantees are classified as credit
derivatives whose fair values were not significant, and the one figure it quantifies is a maximum loss
exposure of $4.7bn in variable interest entities [8].

The three companies are doing the same thing. One publishes the ceiling, one publishes the ceiling and the
formula, and one publishes a fair value close to zero in the statements and the ceiling in a separate
event filing. Whoever reads the three quarterly statements side by side is not reading comparable numbers.

## Meta's signed but unstarted leases grew fourteenfold in two years

Meta discloses each quarter the leases it has signed that have not yet commenced, which sit outside the
balance sheet. In billions of dollars: 7.1 (Dec 2023), 6.2, 6.2, 18.5 (Sep 2024), 34.1 (Dec 2024), 35.3,
52.6, 58.1, 103.8 (Dec 2025) [9]. Fourteen times in two years. Meta also discloses residual value
guarantees with an aggregate threshold of approximately $28bn, stating that payments are not probable and
no liability has been recorded, and a further guarantee of up to $13bn in its filing of 30 July 2026 [10].

## A correlation network cannot see a coupling that pays only on default

[FIGURA2]

These guarantees create a link between two companies that does not exist in their price co-movement until
it triggers. Nvidia and OpenAI are connected by an obligation capped at $105bn that activates only on
tenant insolvency or non-payment, and only after the lessor has pursued a replacement tenant or a sale.
Until then, no correlation measured on market data can see it. The coupling is conditional, and conditional
coupling does not price until it happens.

That is a limitation of my own August measurement and of any measurement of this kind. The fall in the
chain's coupling that I recorded for 2026 admits two readings, not one: the chain decoupling, or exposure
leaving the listed perimeter. These data do not separate them.

## The landlords and the electrical chain state they do none of this

Digital Realty states in eleven consecutive filings that its leases contain no residual value guarantees.
Vertiv states it has no guarantees or off-balance-sheet financing arrangements. Eaton states it has no
off-balance-sheet arrangements with unconsolidated entities. CoreWeave states it has no lease arrangements
with residual value guarantees. The mechanism sits with the buyers of compute and with two chipmakers, not
with the landlords or the electrical chain.

## The risk has changed shape, and the disclosure has not kept up

Nothing described here is hidden. Every figure in this note comes from a document the company filed and
published. The difficulty is not concealment, it is comparability: three companies with the same
obligation report a ceiling, a ceiling with its formula, and a fair value close to zero, and two of them
put it in the quarterly accounts while the third puts the number in the filing made on the day of the
deal. An analyst who wants the total for the sector has to know that each of the three means something
different, and go looking in three different places.

The shape of the risk has changed as well. A decade of data centre building was financed on the balance
sheets of companies that generate cash. A large part of the current build is financed by third parties and
tied back to those companies by promises that pay only if a tenant defaults. That does not make the risk
larger or smaller, and this note takes no view on whether the investment as a whole is sound. What it does
is concentrate the risk on a small number of points of failure, and those points are the tenants: firms
whose ability to pay two decades of leases is precisely what is under debate.

For anyone measuring this from market data, including me, the consequence is concrete. A correlation
network sees companies that move together today. It does not see an obligation of $105bn that is worth
nothing until the day it is worth everything. So the fall in the coupling of the chain that I recorded for
2026 admits two readings, and these data do not separate them: the chain decoupling, or exposure leaving
the listed perimeter. Separating them requires reading the filings, which is what this note starts to do.

There is a straightforward remedy, and it is not more regulation but more comparability: the maximum
potential payment, disclosed every quarter, by everyone who gives one of these guarantees. Two of the
three companies already do it. The number exists in all three cases; what varies is where it is put.

## Method

Full-text search of EDGAR for 21 terms across 13 companies, forms 10-K, 10-Q and 8-K filed between
January 2024 and September 2026, followed by sentence-level extraction of every match with its amounts and
surrounding sentences. 279 filings, 1,187 matching sentences. Every figure quoted above was read in the
filing text and is linked to its source document in the accompanying data files. Code and data accompany this note:
`extraer_garantias_v2.py` (extractor), `garantias_v2_frases.csv` (1,187 sentences with amounts, context and
source link for each), `garantias_v2_aristas.csv` (guarantor and counterparty pairs), `meta_arrendamientos.csv`
and `alphabet_respaldos.csv` (the two series plotted in Figure 2).

Two known gaps. The extractor reads the main document of each filing and not its exhibits, which is why
the Nvidia figure had to be recovered from the 8-K body and its exhibit separately. And amounts are taken
from the sentence in which they appear, so any figure to be quoted must be verified in the source, as was
done for all figures in this note.

## References

1. Acedo, A. (2026). Chips and Megawatts: a network measurement of the AI supply chain. SSRN 7307362. https://ssrn.com/abstract=7307362
2. McMorrow, R., Chan, M., Taffe, M. (2026). Big Tech uses guarantees to keep $300bn of AI exposure off balance sheets. Financial Times, 20 September. https://www.ft.com/content/7f11afae-c4e3-4054-a65b-873f3647f563
3. Alphabet Inc. Form 10-K, filed 5 February 2026. https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm
4. Alphabet Inc. Form 10-Q, filed 30 April 2026. https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm
5. Alphabet Inc. Form 10-Q, filed 23 July 2026. https://www.sec.gov/Archives/edgar/data/1652044/000165204426000071/goog-20260630.htm
6. Broadcom Inc. Form 10-Q, filed 10 September 2026. https://www.sec.gov/Archives/edgar/data/1730168/000173016826000080/avgo-20260802.htm
7. NVIDIA Corp. Form 8-K, filed 17 August 2026. https://www.sec.gov/Archives/edgar/data/1045810/000104581026000069/nvda-20260817.htm
8. NVIDIA Corp. Form 10-Q, filed 26 August 2026. https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm
9. Meta Platforms Inc. Forms 10-K and 10-Q, February 2024 to January 2026. Series and links in `meta_arrendamientos.csv`; first and last: https://www.sec.gov/Archives/edgar/data/1326801/000132680124000012/meta-20231231.htm and https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm
10. Meta Platforms Inc. Form 10-Q, filed 30 July 2026. https://www.sec.gov/Archives/edgar/data/1326801/000162828026050705/meta-20260630.htm
11. Bank for International Settlements (2026). Annual Economic Report, June 2026.
