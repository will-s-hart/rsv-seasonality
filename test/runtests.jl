using RSVSeasonality
using Test

@testset "Japan reported counts and site coverage" begin
    sites = SentinelSites(3, ReportingUnknown)
    incomplete = SentinelSites(3, ReportingIncomplete)
    complete = SentinelSites(3, ReportingComplete)
    unknown_network = SentinelSites(missing, ReportingUnknown)
    absent = JapanObservation(missing, sites)
    observed = JapanObservation(10, sites)
    zero_reports = JapanObservation(0, unknown_network)
    model = NB2(6, 2)

    @test observed.cases == 10
    @test observed.sites.network_sites == 3
    @test observed.sites.reporting == ReportingUnknown
    @test ismissing(zero_reports.sites.network_sites)
    @test ismissing(observation_loglikelihood(absent, model))
    @test ismissing(observation_loglikelihood(absent, model;
        coverage_adjustment=(obs, mu) -> error("no observed count")))
    @test observation_loglikelihood(zero_reports, model) ≈ log(1 / 16)
    @test observation_loglikelihood(observed, model) ≈ log(11 * (3 / 4)^10 / 16)
    @test observation_loglikelihood(JapanObservation(10, incomplete), model) ==
          observation_loglikelihood(JapanObservation(10, complete), model)

    # An explicit scenario can use independently known reporting status and
    # network size. This arbitrary fixture rule is supplied by the caller.
    adjustment = (obs, mu) -> obs.sites.reporting == ReportingIncomplete ?
        mu / obs.sites.network_sites : mu
    @test observation_loglikelihood(JapanObservation(10, incomplete), model;
        coverage_adjustment=adjustment) ≈ log(11 * (1 / 2)^10 / 4)
    @test observation_loglikelihood(observed, model; coverage_adjustment=adjustment) ==
          observation_loglikelihood(observed, model)
    for bad_mean in (-1, Inf, NaN, missing, 1im, true)
        @test_throws ArgumentError observation_loglikelihood(observed, model;
            coverage_adjustment=(obs, mu) -> bad_mean)
    end

    @test_throws ArgumentError SentinelSites(0, ReportingUnknown)
    @test_throws ArgumentError SentinelSites(-1, ReportingComplete)
    @test_throws MethodError SentinelSites(3, :incomplete)
    @test_throws ArgumentError JapanObservation(-1, sites)
    @test_throws ArgumentError JapanObservation(true, sites)
    @test_throws ArgumentError JapanObservation(big(typemax(Int)) + 1, sites)
    @test_throws MethodError JapanObservation(1.5, sites)
    @test_throws MethodError JapanObservation(2, ReportedTests(PCR, 3))
    @test_throws MethodError observation_loglikelihood(observed, BinomialPositivity(0.2))
end

@testset "US method, coverage and outlier flag" begin
    absent = USObservation(Antigen, missing, ReportedTests(Antigen, missing))
    untested = USObservation(Antigen, 0, ReportedTests(Antigen, 0); source_outlier=false)
    true_zero = USObservation(PCR, 0, ReportedTests(PCR, 10); source_outlier=true)
    observed = USObservation(Antigen, 3, ReportedTests(Antigen, 10))

    @test lab_coverage(absent) == AbsentWeek
    @test lab_coverage(untested) == ZeroTestWeek
    @test lab_coverage(true_zero) == TestedWeek
    @test ismissing(observed_positivity(absent))
    @test ismissing(observed_positivity(untested))
    @test observed_positivity(true_zero) == 0
    @test observed_positivity(observed) == 0.3
    @test ismissing(absent.positives) && ismissing(absent.denominator.tests)
    @test untested.positives == untested.denominator.tests == 0
    @test ismissing(absent.source_outlier)
    @test untested.source_outlier === false
    @test true_zero.source_outlier === true
    @test ismissing(observed.source_outlier)
    @test observed.method == Antigen
    @test true_zero.denominator.method == PCR

    for model in (BinomialPositivity(0.3), BetaBinomialPositivity(0.3, 4))
        @test ismissing(observation_loglikelihood(absent, model))
        @test ismissing(observation_loglikelihood(untested, model))
        @test isfinite(observation_loglikelihood(true_zero, model))
        unflagged = USObservation(PCR, 0, ReportedTests(PCR, 10); source_outlier=false)
        @test observation_loglikelihood(true_zero, model) ==
              observation_loglikelihood(unflagged, model)
    end

    @test_throws ArgumentError USObservation(PCR, 3, ReportedTests(Antigen, 10))
    @test_throws ArgumentError USObservation(PCR, missing, ReportedTests(Antigen, missing))
    @test_throws ArgumentError USObservation(PCR, missing, ReportedTests(PCR, 10))
    @test_throws ArgumentError USObservation(PCR, 0, ReportedTests(PCR, missing))
    @test_throws ArgumentError USObservation(PCR, missing, ReportedTests(PCR, missing);
        source_outlier=false)
    @test_throws ArgumentError USObservation(PCR, 1, ReportedTests(PCR, 0))
    @test_throws ArgumentError USObservation(PCR, 11, ReportedTests(PCR, 10))
    @test_throws ArgumentError USObservation(PCR, -1, ReportedTests(PCR, 10))
    @test_throws ArgumentError USObservation(PCR, false, ReportedTests(PCR, 10))
    @test_throws ArgumentError ReportedTests(PCR, -1)
    @test_throws ArgumentError ReportedTests(PCR, true)
    @test_throws MethodError ReportedTests(PCR, 2.0)
    @test_throws MethodError ReportedTests(:PCR, 10)
    @test_throws MethodError USObservation(PCR, 1, SentinelSites(10, ReportingUnknown))
    @test_throws MethodError observation_loglikelihood(observed, NB2(1, 1))
end

@testset "Parameter domain and point masses" begin
    for value in (-1, Inf, -Inf, NaN, true)
        @test_throws ArgumentError NB2(value, 1)
    end
    for value in (0, -1, Inf, -Inf, NaN, true)
        @test_throws ArgumentError NB2(1, value)
        @test_throws ArgumentError BetaBinomialPositivity(0.2, value)
    end
    for value in (-0.01, 1.01, Inf, -Inf, NaN, false)
        @test_throws ArgumentError BinomialPositivity(value)
        @test_throws ArgumentError BetaBinomialPositivity(value, 1)
    end

    sites = SentinelSites(2, ReportingUnknown)
    @test observation_loglikelihood(JapanObservation(0, sites), NB2(0, 1)) == 0
    @test observation_loglikelihood(JapanObservation(1, sites), NB2(0, 1)) == -Inf
    denominator = ReportedTests(PCR, 3)
    for model in (BinomialPositivity(0), BetaBinomialPositivity(0, 1))
        @test observation_loglikelihood(USObservation(PCR, 0, denominator), model) == 0
        @test observation_loglikelihood(USObservation(PCR, 1, denominator), model) == -Inf
    end
    for model in (BinomialPositivity(1), BetaBinomialPositivity(1, 1))
        @test observation_loglikelihood(USObservation(PCR, 3, denominator), model) == 0
        @test observation_loglikelihood(USObservation(PCR, 2, denominator), model) == -Inf
    end
end

@testset "Analytical masses and normalization" begin
    sites = SentinelSites(2, ReportingUnknown)
    # NB2 with phi = mu = 1/2 and success parameter 1/2.
    probabilities = (1 / sqrt(2), 1 / (4sqrt(2)), 3 / (32sqrt(2)))
    for (count, mass) in enumerate(probabilities)
        @test observation_loglikelihood(JapanObservation(count - 1, sites), NB2(0.5, 0.5)) ≈
              log(mass)
    end
    @test sum(exp(observation_loglikelihood(JapanObservation(k, sites), NB2(4, 2)))
              for k in 0:200) ≈ 1

    # Exact rational products give independent reference masses.
    rising_product(x, n) = prod((x + i for i in 0:(n - 1)); init=one(x))
    n = 12
    p = big(2) // 5
    concentration = big(7) // 3
    alpha, beta = p * concentration, (1 - p) * concentration
    tests = ReportedTests(Antigen, n)
    count_mass = Float64[]
    overdispersed_mass = Float64[]
    for k in 0:n
        obs = USObservation(Antigen, k, tests)
        binomial_mass = binomial(n, k) * p^k * (1 - p)^(n - k)
        beta_binomial_mass = binomial(n, k) * rising_product(alpha, k) *
            rising_product(beta, n - k) / rising_product(alpha + beta, n)
        binomial_log = observation_loglikelihood(obs, BinomialPositivity(Float64(p)))
        beta_binomial_log = observation_loglikelihood(obs,
            BetaBinomialPositivity(Float64(p), Float64(concentration)))
        @test binomial_log ≈ Float64(log(BigFloat(binomial_mass)))
        @test beta_binomial_log ≈ Float64(log(BigFloat(beta_binomial_mass)))
        push!(count_mass, exp(binomial_log))
        push!(overdispersed_mass, exp(beta_binomial_log))
    end
    @test sum(count_mass) ≈ 1
    @test sum(overdispersed_mass) ≈ 1
end

@testset "Numerical limits" begin
    sites = SentinelSites(2, ReportingUnknown)
    @test observation_loglikelihood(JapanObservation(2, sites), NB2(3, 1e300)) ≈
          -3 + log(9 / 2)
    @test observation_loglikelihood(JapanObservation(0, sites), NB2(1e-100, 1e300)) ≈ -1e-100
    @test isfinite(observation_loglikelihood(JapanObservation(1, sites), NB2(1e300, 1e-300)))

    obs = USObservation(PCR, 3, ReportedTests(PCR, 10))
    @test observation_loglikelihood(obs, BetaBinomialPositivity(0.3, 1e300)) ≈
          observation_loglikelihood(obs, BinomialPositivity(0.3))
    @test observation_loglikelihood(obs, BinomialPositivity(nextfloat(0.0))) ≈
          log(120) + 3 * log(nextfloat(0.0))
    one_test = USObservation(PCR, 1, ReportedTests(PCR, 1))
    @test observation_loglikelihood(one_test, BetaBinomialPositivity(1e-200, 1e-200)) ≈
          log(1e-200)
    all_positive = USObservation(PCR, 10, ReportedTests(PCR, 10))
    @test observation_loglikelihood(all_positive, BetaBinomialPositivity(0.3, 1e-300)) ≈
          log(0.3)

    # A uniform beta mixture gives a uniform discrete count distribution.
    n = 100_000
    broad = USObservation(Antigen, div(n, 2), ReportedTests(Antigen, n))
    @test observation_loglikelihood(broad, BetaBinomialPositivity(0.5, 2)) ≈ -log(n + 1)

    # Model parameters and evaluation can retain caller-supplied precision.
    result = observation_loglikelihood(USObservation(PCR, 1, ReportedTests(PCR, 2)),
        BetaBinomialPositivity(BigFloat("0.5"), big"2"))
    @test result isa BigFloat
    @test result ≈ -log(BigFloat(3))

    # Conversion of an interior rational must preserve the support.
    p = (typemax(Int) - 1) // typemax(Int)
    one_negative = USObservation(PCR, 0, ReportedTests(PCR, 1))
    for model in (BinomialPositivity(p), BetaBinomialPositivity(p, 2))
        @test 0 < model.p < 1
        @test observation_loglikelihood(one_negative, model) ≈ log(BigFloat(1 - p))
    end
    setprecision(BigFloat, 128) do
        too_close = 1 - 1 // big(2)^256
        @test_throws ArgumentError BinomialPositivity(too_close)
        @test_throws ArgumentError BetaBinomialPositivity(too_close, 2)
    end
    setprecision(BigFloat, 32) do
        @test_throws ArgumentError BetaBinomialPositivity(prevfloat(1.0), BigFloat(2))
    end

    precise_models = setprecision(BigFloat, 256) do
        p = 1 - BigFloat(2)^(-200)
        (BinomialPositivity(p), BetaBinomialPositivity(p, 2))
    end
    setprecision(BigFloat, 128) do
        for model in precise_models
            @test observation_loglikelihood(one_negative, model) ≈ -200 * log(BigFloat(2))
        end
    end
end
