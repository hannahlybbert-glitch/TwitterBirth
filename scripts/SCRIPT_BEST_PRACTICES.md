
Author: Hannah Lybbert

Created: 02/09/2026

Purpose: Script best practices for claude code to reference

Hi Claude, these are the best practices I want you to follow as you build/edit scripts in the Twitter Project

1. Do not edit anything in the /data/raw/ folder

2. In all scripts please include at the header:

For Python :
```
# Author: Hannah Lybbert (or if it's a different author indicate that here)
# Created: Date created
# Updated: Date updated
# Purpose: a short, one line indicator of what the script does
```

For STATA:
```
* Author: Hannah Lybbert (or if it's a different author indicate that here)
* Created: Date created
* Updated: Date updated
* Purpose: a short, one line indicator of what the script does
```

3. Naming convention for figures should be 

`[outcome]_[split].jpg`

We want them to be very informative. If the strategy used logs (log) or fixed effects (fe) make sure to specify that in the file name as well. (ex. log_orig_tweets.jpg, or log_orig_tweets_gender.jpg)

4. Use Globals/variables as often as possible

When we will reuse similar code for lots of tasks, this great way to simplify work. When it makes sense but as often as possible to simplify work that could be generalized to follow the same variables

5. For all scripts in /Reddit/ use addaptive paths so we can run on the cluster

6. Keep comments short. No long intro headers or essay-style comments.

- The header is only the four lines in item 2. Purpose is one line. No DESIGN, Usage, Input/Output, or rationale blocks under it.
- Organize the body into clear, labeled sections (`# 1. ...`, `# A. ...`, or just a short label). One line per section label; add a second line only if something is genuinely non-obvious.
- Inline comments only where the code isn't self-explanatory, and one line each.
- No history ("changed on X", "was Y before"), no explanations of what was considered and rejected, no restating what the code already says.
- Reference example: `Reddit/scripts/py/data_prep/process_llm/extract_2_3M_births.py`
- Exception: a genuinely complex script (or step) can get more detail where it's needed to understand it. That's the exception, not the default.