from alg import optCharger, moer

m = moer.Moer(
    mu=[10, 10, 10, 1, 13, 3, 2, 3],
    isDiagonal=True,
)
print(len(m))

print("No extra costs ... ")
model = optCharger.OptCharger(
    fixedChargeRate=1,
)
model.fit(totalCharge=3, totalTime=8, moer=m, optimization_method="baseline")
model.summary()

# simple, assumes a 1 kW
model.fit(totalCharge=3, totalTime=8, moer=m, optimization_method="simple")
model.summary()

# fixed charge rate
model.fit(
    totalCharge=3,
    totalTime=8,
    moer=m,
    optimization_method="sophisticated",
    emission_multiplier_fn=lambda x, y: [2.0, 2.0, 2.0][x],
)
model.summary()

# incorrect pairing of simple sorting algo + variable charge rate
model.fit(
    totalCharge=3,
    totalTime=8,
    moer=m,
    optimization_method="simple",
    emission_multiplier_fn=lambda x, y: [1.0, 2.0, 1.0][x],
)
model.summary()

# correct pairing of dynamic sorting algo + variable charge rate
model.fit(
    totalCharge=3,
    totalTime=8,
    moer=m,
    optimization_method="auto",
    emission_multiplier_fn=lambda x, y: [1.0, 2.0, 1.0][x],
)
model.summary()

model.fit(
    totalCharge=3,
    totalTime=8,
    moer=m,
    optimization_method="auto",
    constraints={0: (1, None), 1: (2, None)},
)
model.summary()

model.fit(
    totalCharge=3, totalTime=8, moer=m, optimization_method="auto", totalIntervals=1
)
model.summary()

print ("One contiguous interval + variable power rate")
model.fit(
    totalCharge=3,
    totalTime=8,
    moer=m,
    optimization_method="auto",
    totalIntervals=1,
    emission_multiplier_fn=lambda x, y: [1.0, 0.1, 1.0][x],
)

model.summary()

print ("Two contiguous intervals, must charge 1st time period, variable power rate")
model.fit(
    totalCharge=3,
    totalTime=8,
    moer=m,
    optimization_method="auto",
    totalIntervals=2,
    constraints={0: (1, None)},
    emission_multiplier_fn=lambda x, y: [1.0, 0.1, 1.0][x]
)
model.summary()