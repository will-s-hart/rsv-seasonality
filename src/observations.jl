@enum SentinelReporting ReportingUnknown ReportingIncomplete ReportingComplete
@enum LabMethod PCR Antigen
@enum LabCoverage AbsentWeek ZeroTestWeek TestedWeek

function _count(value::Integer)
    if value isa Bool || !(0 <= value <= typemax(Int))
        throw(ArgumentError("counts must be nonnegative integers representable as Int"))
    end
    return Int(value)
end
_count(::Missing) = missing

"""
    SentinelSites(network_sites, reporting::SentinelReporting)

NESID's weekly paediatric sentinel network size, as a positive count or
`missing`. The separate reporting status describes weekly RSV reporting by
that network. Use `ReportingUnknown` when only the network size is available.
"""
struct SentinelSites
    network_sites::Union{Int, Missing}
    reporting::SentinelReporting

    function SentinelSites(network_sites::Union{Integer, Missing}, reporting::SentinelReporting)
        sites = _count(network_sites)
        sites === 0 && throw(ArgumentError("known sentinel network size must be positive"))
        return new(sites, reporting)
    end
end

"""
    JapanObservation(cases, sites::SentinelSites)

Reported paediatric RSV case counts for a NESID diagnosis week. A missing case
count means there is no count observation. A reported zero is a count, and
multiple reports per sentinel site are possible.
"""
struct JapanObservation
    cases::Union{Int, Missing}
    sites::SentinelSites

    function JapanObservation(cases::Union{Integer, Missing}, sites::SentinelSites)
        return new(_count(cases), sites)
    end
end

"""
    ReportedTests(method::LabMethod, tests)

NREVSS's actual reported tests for the named diagnostic method. Use
`missing` for an absent source row and zero for an explicit zero-test row.
"""
struct ReportedTests
    method::LabMethod
    tests::Union{Int, Missing}

    function ReportedTests(method::LabMethod, tests::Union{Integer, Missing})
        return new(method, _count(tests))
    end
end

"""
    USObservation(method::LabMethod, positives, denominator::ReportedTests;
                  source_outlier=missing)

NREVSS detections and reported tests from the same method and reporting week.
For an absent row, positives, tests and the source outlier flag must all be
`missing`. Otherwise, positives and tests must both be counts. The optional
native outlier flag is `true`, `false`, or `missing`.
"""
struct USObservation
    method::LabMethod
    positives::Union{Int, Missing}
    denominator::ReportedTests
    source_outlier::Union{Bool, Missing}

    function USObservation(method::LabMethod, positives::Union{Integer, Missing},
                           denominator::ReportedTests; source_outlier::Union{Bool, Missing}=missing)
        method == denominator.method ||
            throw(ArgumentError("detections and tests must use the same diagnostic method"))
        count = _count(positives)
        tests = denominator.tests
        ismissing(count) == ismissing(tests) ||
            throw(ArgumentError("positives and tests must both be present or both missing"))
        if ismissing(tests)
            ismissing(source_outlier) ||
                throw(ArgumentError("an absent source row cannot have an outlier flag"))
        elseif count > tests
            throw(ArgumentError("positives cannot exceed reported tests"))
        end
        return new(method, count, denominator, source_outlier)
    end
end

"""
    lab_coverage(obs::USObservation)

Distinguish `AbsentWeek`, source-present `ZeroTestWeek`, and `TestedWeek`.
"""
function lab_coverage(obs::USObservation)
    tests = obs.denominator.tests
    ismissing(tests) && return AbsentWeek
    return iszero(tests) ? ZeroTestWeek : TestedWeek
end

"""
    observed_positivity(obs::USObservation)

Return detections divided by reported tests for a tested week, or `missing`
for absent and zero-test weeks.
"""
function observed_positivity(obs::USObservation)
    lab_coverage(obs) == TestedWeek || return missing
    return obs.positives / obs.denominator.tests
end

function _nonnegative_mean(mu::Real)
    if mu isa Bool || !isfinite(mu) || mu < 0
        throw(ArgumentError("the expected reported count must be finite and nonnegative"))
    end
    return mu
end

function _probability_float(p::Real)
    if p isa Bool || !isfinite(p) || !(0 <= p <= 1)
        throw(ArgumentError("the test-positive probability must be in [0, 1]"))
    end
    probability = _parameter_float(p)
    if 0 < p < 1 && !(0 < probability < 1)
        probability = BigFloat(p)
        0 < probability < 1 ||
            throw(ArgumentError("an interior probability rounded to a boundary; supply higher precision"))
    end
    return probability
end

function _positive_dispersion(value::Real)
    if value isa Bool || !isfinite(value) || value <= 0
        throw(ArgumentError("dispersion or concentration must be finite and positive"))
    end
    return value
end

# Use at least Float64 for summing log factors, while retaining BigFloat inputs.
_parameter_float(value::Real) = promote(float(value), 0.0)[1]

"""
    NB2(mu, phi)

Negative binomial for reported counts with mean `mu` (expected reported
cases in the week) and variance `mu + mu^2 / phi`. The dimensionless shape
`phi` is finite and positive. A zero mean puts all mass on zero; increasing
`phi` at fixed mean approaches the Poisson limit.
"""
struct NB2{T<:AbstractFloat}
    mu::T
    phi::T

    function NB2(mu::Real, phi::Real)
        mean, shape = promote(_parameter_float(_nonnegative_mean(mu)),
                              _parameter_float(_positive_dispersion(phi)))
        _nonnegative_mean(mean)
        _positive_dispersion(shape)
        return new{typeof(mean)}(mean, shape)
    end
end

"""
    BinomialPositivity(p)

Binomial model conditional on the actual number of tests of one method.
`p` is the caller-supplied probability of a positive test, in `[0, 1]`.
"""
struct BinomialPositivity{T<:AbstractFloat}
    p::T

    function BinomialPositivity(p::Real)
        probability = _probability_float(p)
        return new{typeof(probability)}(probability)
    end
end

"""
    BetaBinomialPositivity(p, concentration)

Beta-binomial model with mean test-positive probability `p` and dimensionless,
finite positive `concentration`. The beta shapes are `p * concentration` and
`(1 - p) * concentration`, with within-week correlation `1 / (1 + concentration)`.
At `p = 0` or `p = 1`, use the point-mass limit.
"""
struct BetaBinomialPositivity{T<:AbstractFloat}
    p::T
    concentration::T

    function BetaBinomialPositivity(p::Real, concentration::Real)
        probability, shape = promote(_probability_float(p),
                                     _parameter_float(_positive_dispersion(concentration)))
        _positive_dispersion(shape)
        return new{typeof(probability)}(probability, shape)
    end
end

"""
    observation_loglikelihood(obs::JapanObservation, model::NB2; coverage_adjustment=nothing)
    observation_loglikelihood(obs::USObservation, model::Union{BinomialPositivity, BetaBinomialPositivity})

Return the log probability of the reported response, or `missing` when
there is no observed count (Japan) or no tested week (US). Impossible counts
under a point-mass model have log probability `-Inf`.

For Japan, an optional callable receives `(obs, model.mu)` and must return
the finite, nonnegative expected reported count under the caller's coverage
scenario. It is called only for observed counts and changes only the mean.
The supplied mean is used directly when the callable is omitted.
"""
function observation_loglikelihood(obs::JapanObservation, model::NB2; coverage_adjustment=nothing)
    ismissing(obs.cases) && return missing
    mu = model.mu
    if coverage_adjustment !== nothing
        adjusted = coverage_adjustment(obs, mu)
        adjusted isa Real || throw(ArgumentError("coverage adjustment must return a real mean"))
        model = NB2(adjusted, model.phi)
    end
    return _nb2_logmass(obs.cases, model.mu, model.phi)
end

function observation_loglikelihood(obs::USObservation,
                                   model::Union{BinomialPositivity, BetaBinomialPositivity})
    lab_coverage(obs) == TestedWeek || return missing
    p = model.p
    successes = obs.positives
    tests = obs.denominator.tests
    iszero(p) && return iszero(successes) ? zero(p) : oftype(p, -Inf)
    isone(p) && return successes == tests ? zero(p) : oftype(p, -Inf)
    return _test_logmass(successes, tests - successes, model)
end

function _nb2_logmass(count, mu, phi)
    iszero(mu) && return iszero(count) ? zero(mu) : oftype(mu, -Inf)

    # Compute the zero-count term without forming phi + mu or a large mu / phi.
    ratio = min(mu, phi) / max(mu, phi)
    if mu <= phi
        zero_logmass = iszero(ratio) ? -mu : -mu * (log1p(ratio) / ratio)
    else
        zero_logmass = -phi * (log(mu) - log(phi) + log1p(ratio))
    end
    iszero(count) && return zero_logmass

    # The successive mass ratio at i is (phi + i - 1) / i * mu / (phi + mu).
    # Separate the i = 1 term and combine factors before summing their logs.
    first_step = log(min(mu, phi)) - log1p(ratio)
    if phi >= 1
        rest = sum(i -> first_step + log1p((i - 1) / phi) - log(oftype(mu, i)),
                   2:count; init=zero(mu))
    else
        log_step_scale = mu >= phi ? -log1p(ratio) : log(mu) - log(phi) - log1p(ratio)
        rest = sum(i -> log_step_scale + log1p((phi - 1) / i), 2:count; init=zero(mu))
    end
    return zero_logmass + first_step + rest
end

function _logchoose(successes, failures, p)
    smaller, larger = minmax(successes, failures)
    return sum(i -> log1p(oftype(p, larger) / i), 1:smaller; init=zero(p))
end

function _test_logmass(successes, failures, model::BinomialPositivity)
    p = model.p
    return _logchoose(successes, failures, p) + successes * log(p) + failures * log1p(-p)
end

_softplus(x) = max(x, zero(x)) + log1p(exp(-abs(x)))
_logaddexp(x, y) = max(x, y) + log1p(exp(-abs(x - y)))

function _test_logmass(successes, failures, model::BetaBinomialPositivity)
    p = model.p
    log_concentration = log(model.concentration)
    log_alpha = log(p) + log_concentration
    log_beta = log1p(-p) + log_concentration

    # Factor the probability of one order (successes followed by failures) into
    # conditional probabilities, then count the orders. Use log weights so
    # small positive beta shapes do not round to zero.
    success_terms = sum(0:(successes - 1); init=zero(p)) do i
        log_success_weight = _logaddexp(log_alpha, log(oftype(p, i)))
        -_softplus(log_beta - log_success_weight)
    end
    log_success_weight = _logaddexp(log_alpha, log(oftype(p, successes)))
    failure_terms = sum(0:(failures - 1); init=zero(p)) do i
        log_failure_weight = _logaddexp(log_beta, log(oftype(p, i)))
        -_softplus(log_success_weight - log_failure_weight)
    end
    return _logchoose(successes, failures, p) + success_terms + failure_terms
end
