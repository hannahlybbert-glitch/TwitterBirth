
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