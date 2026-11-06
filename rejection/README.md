# rejection

**What it does:** Works out whether price has been rejected at a level or band (for example, pierced it and then turned back). It is shared by the analyser, the strategies and the trade manager, so all three use the same definition of a rejection.

**What it must never do:** Never place, change or close a trade. Never keep its own private copy of the rules for a single user: there is one rejection check, used by everyone.
