# Mediator horse-race (temporal design)

Content classes measured in the OPENING rounds; outcome is the CLOSING half. Controls: how the opening actually went, private channel, demand spec.

Free-text matches with >=6 rounds: 1070


## Base rates of each content class in opening rounds

| class | IPD | Bertrand |
|---|---:|---:|
| open_threat | 0.124 | 0.002 |
| open_agreement | 0.785 | 0.916 |
| open_affirm | 0.911 | 0.664 |
| open_solicit | 0.360 | 0.862 |


## IPD — closing-half cooperation

### IPD closing cooperation — n=484 free-text matches

| term | coef | 95% CI | base rate |
|---|---:|---|---:|
| intercept ** | +0.589 | [+0.456, +0.720] |  |
| open_threat | +0.028 | [-0.046, +0.102] | 0.12 |
| open_agreement | -0.051 | [-0.128, +0.025] | 0.79 |
| open_affirm | +0.109 | [-0.017, +0.244] | 0.91 |
| open_solicit | -0.012 | [-0.068, +0.045] | 0.36 |
| open_len(z) | -0.014 | [-0.050, +0.019] |  |
| open_coop(z) ** | +0.223 | [+0.192, +0.251] |  |
| private ** | +0.104 | [+0.043, +0.161] |  |
| novel_spec | -0.078 | [-0.181, +0.018] |  |


## Bertrand — closing-half K

### Bertrand closing K — n=500 free-text matches

| term | coef | 95% CI | base rate |
|---|---:|---|---:|
| intercept ** | +1.146 | [+0.927, +1.373] |  |
| open_threat | +2.483 | [-0.000, +2.641] | 0.00 |
| open_agreement ** | -0.087 | [-0.188, -0.000] | 0.92 |
| open_affirm | -0.028 | [-0.096, +0.040] | 0.66 |
| open_solicit ** | +0.133 | [+0.031, +0.247] | 0.86 |
| open_len(z) ** | -0.058 | [-0.093, -0.023] |  |
| open_price(z) ** | +0.326 | [+0.272, +0.387] |  |
| private | +0.025 | [-0.046, +0.097] |  |
| novel_spec ** | -0.981 | [-1.212, -0.765] |  |