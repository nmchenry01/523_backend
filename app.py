from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from data import pull_data, get_risk_free_rate, calculate_returns
from portfolio import Portfolio
from benchmark import Benchmark
import pandas as pd
import re

app = Flask(__name__)
CORS(app)

#Initial test method
@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello World'

@app.route('/api/info', methods=['POST']) 
def parse_info():   

    #check date is valid format
    pattern = re.compile("^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$")
    if not pattern.fullmatch(request.get_json()['start_date']):
        abort(400)
    if not pattern.fullmatch(request.get_json()['end_date']):
        abort(400)

    stocks = request.get_json()['assets']
    benchmark = request.get_json()['benchmark'] #Needs to be a list
    start_date = pd.to_datetime(request.get_json()['start_date']) #Datetime object
    end_date = pd.to_datetime(request.get_json()['end_date'])
    frequency = request.get_json()['frequency']
    transaction_costs = request.get_json()['transaction_costs'] #0 or 1

    #is date valid range?  
    #Error code 1
    if start_date >= end_date:
        return jsonify({
            "Error Code" : "1",
            "Error Description" : "Inverted Date Range"
        })

    #Used for date interval checking
    date_diff = end_date - start_date
        
    #Error code 2
    if frequency == "monthly" and date_diff.days > 731: #2 years worth of days
        return jsonify({
            "Error Code" : "2",
            "Error Description" : "Too long of a date range (monthly). Please enter a range interval between 4 months and 2 years"
        })

    #Error code 3
    if frequency == "quarterly" and date_diff.days > 1461: #4 years worth of days
        return jsonify({
            "Error Code" : "3",
            "Error Description" : "Too long of a date range (quarterly). Please enter a range interval between 1 year and 4 years"
        })

    #Error code 4
    if frequency == "biannual" and date_diff.days > 2922: #4 years worth of days
        return jsonify({
            "Error Code" : "4",
            "Error Description" : "Too long of a date range (biannual). Please enter a range interval between 2 year and 8 years"
        })  

    #Error code 5
    if frequency == "monthly" and date_diff.days < 120: #4 months worth of days
        return jsonify({
            "Error Code" : "5",
            "Error Description" : "Too short of a date range (monthly). Please enter a range interval between 4 months and 2 years"
        })     

    #Error code 6
    if frequency == "quarterly" and date_diff.days < 365: #1 year worth of days
        return jsonify({
            "Error Code" : "6",
            "Error Description" : "Too short of a date range (quarterly). Please enter a range interval between 1 year and 4 years"
        })  

    #Error code 7
    if frequency == "biannual" and date_diff.days < 731: #2 years worth of days
        return jsonify({
            "Error Code" : "7",
            "Error Description" : "Too short of a date range (biannual). Please enter a range interval between 2 year and 8 years"
        })          

    #check if is string, make list if string
    if isinstance(benchmark, str):
        benchmark = [benchmark]

    #ensure stocks is list
    if not isinstance(stocks, list) :
        abort(400)

    #Initial data pull
    results = pull_data(stocks, start_date, end_date) 
    benchmark_results = pull_data(benchmark, start_date, end_date)

    #Get daily and annual risk free rate
    interest_rates = get_risk_free_rate(start_date,end_date)

    #Calculate log returns
    return_dict = calculate_returns(results['stock_dict'])
    benchmark_return_dict = calculate_returns(benchmark_results['stock_dict'])

    #Output for the portfolio
    portfolio = Portfolio(start_date, end_date, return_dict, interest_rates, frequency, transaction_costs)
    output = portfolio.optimize_portfolio()

    #Output for the benchmark
    benchmark = Benchmark(benchmark_return_dict,benchmark)
    benchmark_output = benchmark.form_returns()

    #Find matching keys, build joint data structure
    common_keys = set(output['cumulative_returns']).intersection(benchmark_output["benchmark_cumulative_returns"])
    intersect_dict = {}
    for key in common_keys:
        intersect_dict[key] = [output['cumulative_returns'][key],benchmark_output["benchmark_cumulative_returns"][key]]

    #BELOW THIS LINE IS USED FOR TESTING ON LOCALHOST

    return jsonify({"optimized_cumulative_returns": output['cumulative_returns'],
                   "optimized_weights": output['optimized_weights'],
                   "benchmark_portfolio_intersection": intersect_dict,
                   "benchmark_cumulative_returns": benchmark_output['benchmark_cumulative_returns']
                     })
    
@app.route('/api/test', methods=['GET']) 
def test_info():
    
    return jsonify({
    "benchmark_cumulative_returns": [
        [
            "2015/03/31",
            0.0033389012655141784
        ],
        [
            "2015/04/30",
            0.051335099533769656
        ],
        [
            "2015/05/31",
            -0.11225902348553182
        ],
        [
            "2015/06/30",
            -0.18701482722570453
        ],
        [
            "2015/07/31",
            -0.22922387196518743
        ],
        [
            "2015/08/31",
            -0.21253943905728387
        ],
        [
            "2015/09/30",
            -0.6205932102729587
        ],
        [
            "2015/10/31",
            -0.5914723785735696
        ],
        [
            "2015/11/30",
            -0.9447005289232213
        ],
        [
            "2015/12/31",
            -1.0560526742493148
        ],
        [
            "2016/01/31",
            -1.2755969415338775
        ],
        [
            "2016/02/29",
            -1.9392434576971245
        ],
        [
            "2016/03/31",
            -1.7114595268264123
        ]
    ],
    "benchmark_returns": [
        [
            "2015/03/31",
            0.0033389012655141784
        ],
        [
            "2015/04/30",
            0.04799619826825548
        ],
        [
            "2015/05/31",
            -0.16359412301930149
        ],
        [
            "2015/06/30",
            -0.07475580374017271
        ],
        [
            "2015/07/31",
            -0.04220904473948289
        ],
        [
            "2015/08/31",
            0.016684432907903564
        ],
        [
            "2015/09/30",
            -0.40805377121567477
        ],
        [
            "2015/10/31",
            0.029120831699389102
        ],
        [
            "2015/11/30",
            -0.35322815034965166
        ],
        [
            "2015/12/31",
            -0.11135214532609358
        ],
        [
            "2016/01/31",
            -0.21954426728456267
        ],
        [
            "2016/02/29",
            -0.663646516163247
        ],
        [
            "2016/03/31",
            0.22778393087071222
        ]
    ],
    "optimized_cumulative_returns": {
        "2015-03-03": 0.03185776749866967,
        "2015-03-31": 0.07310562762743272,
        "2015-04-30": 0.11470732009772895,
        "2015-05-31": 0.1496605450149145,
        "2015-06-30": 0.19811884291722553,
        "2015-07-31": 0.13078818796725705,
        "2015-08-31": -0.021641441200295652,
        "2015-09-30": 0.021003793564529305,
        "2015-10-31": 0.05264087697706135,
        "2015-11-30": 0.09878888755294014,
        "2015-12-31": 0.1347873119748663,
        "2016-01-31": 0.16642996484531675,
        "2016-02-29": 0.19411615439692853
    },
    "optimized_returns": {
        "2015-03-03": 0.03185776749866967,
        "2015-03-31": 0.041247860128763046,
        "2015-04-30": 0.04160169247029623,
        "2015-05-31": 0.03495322491718553,
        "2015-06-30": 0.04845829790231103,
        "2015-07-31": -0.06733065494996848,
        "2015-08-31": -0.1524296291675527,
        "2015-09-30": 0.04264523476482496,
        "2015-10-31": 0.03163708341253205,
        "2015-11-30": 0.04614801057587879,
        "2015-12-31": 0.035998424421926155,
        "2016-01-31": 0.03164265287045044,
        "2016-02-29": 0.027686189551611794
    },
    "optimized_weights": {
        "2015-03-03": [
            [
                "IBB",
                3.744997841949241e-9,
                "0.000%"
            ],
            [
                "IHE",
                0.41237977957816047,
                "41.238%"
            ],
            [
                "IVV",
                -1.0177477590564965e-8,
                "-0.000%"
            ],
            [
                "IYC",
                3.157518012824118e-9,
                "0.000%"
            ],
            [
                "IYE",
                -5.5812719945232e-9,
                "-0.000%"
            ],
            [
                "IYF",
                -7.134971634944978e-9,
                "-0.000%"
            ],
            [
                "IYH",
                -1.0213712868998023e-9,
                "-0.000%"
            ],
            [
                "IYJ",
                -1.3906766325609915e-8,
                "-0.000%"
            ],
            [
                "IYW",
                -0.5876201738940396,
                "-58.762%"
            ]
        ],
        "2015-03-31": [
            [
                "IBB",
                -9.508838850391556e-8,
                "-0.000%"
            ],
            [
                "IHE",
                -5.947582694229732e-7,
                "-0.000%"
            ],
            [
                "IVV",
                4.521950605501213e-8,
                "0.000%"
            ],
            [
                "IYC",
                4.6107903582004033e-7,
                "0.000%"
            ],
            [
                "IYE",
                0.5068424903947455,
                "50.684%"
            ],
            [
                "IYF",
                -3.3822004086435753e-7,
                "-0.000%"
            ],
            [
                "IYH",
                -0.2835957531885528,
                "-28.360%"
            ],
            [
                "IYJ",
                -0.1944753765907655,
                "-19.448%"
            ],
            [
                "IYW",
                0.015085013007706299,
                "1.509%"
            ]
        ],
        "2015-04-30": [
            [
                "IBB",
                0.26341360937421293,
                "26.341%"
            ],
            [
                "IHE",
                -0.10636283557623359,
                "-10.636%"
            ],
            [
                "IVV",
                -7.666101803028017e-8,
                "-0.000%"
            ],
            [
                "IYC",
                -3.5027771600027344e-7,
                "-0.000%"
            ],
            [
                "IYE",
                -0.4881007727092231,
                "-48.810%"
            ],
            [
                "IYF",
                -1.9711579941173638e-7,
                "-0.000%"
            ],
            [
                "IYH",
                0.10449335744716994,
                "10.449%"
            ],
            [
                "IYJ",
                -0.03762841212728679,
                "-3.763%"
            ],
            [
                "IYW",
                -3.8871134018719813e-7,
                "-0.000%"
            ]
        ],
        "2015-05-31": [
            [
                "IBB",
                0.298749134073575,
                "29.875%"
            ],
            [
                "IHE",
                -5.3033088901718226e-9,
                "-0.000%"
            ],
            [
                "IVV",
                8.39826523176638e-8,
                "0.000%"
            ],
            [
                "IYC",
                1.1100577234738718e-7,
                "0.000%"
            ],
            [
                "IYE",
                -0.010625281995225812,
                "-1.063%"
            ],
            [
                "IYF",
                3.815907586726929e-8,
                "0.000%"
            ],
            [
                "IYH",
                2.5388821963471776e-8,
                "0.000%"
            ],
            [
                "IYJ",
                -2.1063198874171302e-7,
                "-0.000%"
            ],
            [
                "IYW",
                -0.6906256061397195,
                "-69.063%"
            ]
        ],
        "2015-06-30": [
            [
                "IBB",
                0.09025364735867722,
                "9.025%"
            ],
            [
                "IHE",
                -3.891046945341163e-9,
                "-0.000%"
            ],
            [
                "IVV",
                -0.000002385444599921367,
                "-0.000%"
            ],
            [
                "IYC",
                0.4956058782544056,
                "49.561%"
            ],
            [
                "IYE",
                -0.2195472457679856,
                "-21.955%"
            ],
            [
                "IYF",
                -0.0000042735794682859224,
                "-0.000%"
            ],
            [
                "IYH",
                3.5197082246094497e-7,
                "0.000%"
            ],
            [
                "IYJ",
                -0.1945648991614758,
                "-19.456%"
            ],
            [
                "IYW",
                0.000021322834997492167,
                "0.002%"
            ]
        ],
        "2015-07-31": [
            [
                "IBB",
                -8.850039884865094e-9,
                "-0.000%"
            ],
            [
                "IHE",
                2.0794603605349844e-7,
                "0.000%"
            ],
            [
                "IVV",
                1.8947858541348014e-10,
                "0.000%"
            ],
            [
                "IYC",
                9.669814724975808e-8,
                "0.000%"
            ],
            [
                "IYE",
                1,
                "100.000%"
            ],
            [
                "IYF",
                -2.41058351744139e-8,
                "-0.000%"
            ],
            [
                "IYH",
                -4.271587249004737e-8,
                "-0.000%"
            ],
            [
                "IYJ",
                6.216985047182581e-9,
                "0.000%"
            ],
            [
                "IYW",
                1.5592589706117006e-7,
                "0.000%"
            ]
        ],
        "2015-08-31": [
            [
                "IBB",
                0.9999771761301119,
                "99.998%"
            ],
            [
                "IHE",
                5.6439619989767424e-8,
                "0.000%"
            ],
            [
                "IVV",
                2.5397823285984277e-8,
                "0.000%"
            ],
            [
                "IYC",
                1.8784580512218472e-7,
                "0.000%"
            ],
            [
                "IYE",
                2.6326781227716147e-7,
                "0.000%"
            ],
            [
                "IYF",
                0.0000013096184692376403,
                "0.000%"
            ],
            [
                "IYH",
                0.000014371325475940499,
                "0.001%"
            ],
            [
                "IYJ",
                5.112039587277851e-9,
                "0.000%"
            ],
            [
                "IYW",
                0.000006604862842350247,
                "0.001%"
            ]
        ],
        "2015-09-30": [
            [
                "IBB",
                -0.025775253440770397,
                "-2.578%"
            ],
            [
                "IHE",
                -0.26971434197364563,
                "-26.971%"
            ],
            [
                "IVV",
                -2.0482130434911503e-9,
                "-0.000%"
            ],
            [
                "IYC",
                -1.8333049165873426e-9,
                "-0.000%"
            ],
            [
                "IYE",
                0.027615709822710614,
                "2.762%"
            ],
            [
                "IYF",
                -0.027464852960119638,
                "-2.746%"
            ],
            [
                "IYH",
                0.42200470841240256,
                "42.200%"
            ],
            [
                "IYJ",
                2.9586888657288173e-9,
                "0.000%"
            ],
            [
                "IYW",
                0.2274261259929919,
                "22.743%"
            ]
        ],
        "2015-10-31": [
            [
                "IBB",
                3.058737443310353e-7,
                "0.000%"
            ],
            [
                "IHE",
                0.7752169174092967,
                "77.522%"
            ],
            [
                "IVV",
                -2.1889187442938683e-8,
                "-0.000%"
            ],
            [
                "IYC",
                -2.706680949868659e-7,
                "-0.000%"
            ],
            [
                "IYE",
                -0.09241448876536701,
                "-9.241%"
            ],
            [
                "IYF",
                -4.6100155661884815e-8,
                "-0.000%"
            ],
            [
                "IYH",
                -0.13236810262002435,
                "-13.237%"
            ],
            [
                "IYJ",
                1.276197782773891e-7,
                "0.000%"
            ],
            [
                "IYW",
                4.172675190267668e-7,
                "0.000%"
            ]
        ],
        "2015-11-30": [
            [
                "IBB",
                4.3768128424816574e-10,
                "0.000%"
            ],
            [
                "IHE",
                0.25991696871378955,
                "25.992%"
            ],
            [
                "IVV",
                2.3755083544057362e-7,
                "0.000%"
            ],
            [
                "IYC",
                -2.579142710821726e-7,
                "-0.000%"
            ],
            [
                "IYE",
                -0.3856613847441725,
                "-38.566%"
            ],
            [
                "IYF",
                -1.7765068948188357e-8,
                "-0.000%"
            ],
            [
                "IYH",
                0.12884379384549977,
                "12.884%"
            ],
            [
                "IYJ",
                -0.027723589512185894,
                "-2.772%"
            ],
            [
                "IYW",
                -0.197853785046632,
                "-19.785%"
            ]
        ],
        "2015-12-31": [
            [
                "IBB",
                -0.226464124998564,
                "-22.646%"
            ],
            [
                "IHE",
                4.825943002818598e-9,
                "0.000%"
            ],
            [
                "IVV",
                1.450897086521466e-7,
                "0.000%"
            ],
            [
                "IYC",
                -2.865751785215334e-7,
                "-0.000%"
            ],
            [
                "IYE",
                0.04393979573078595,
                "4.394%"
            ],
            [
                "IYF",
                -0.2651764490857566,
                "-26.518%"
            ],
            [
                "IYH",
                0.3493573451417775,
                "34.936%"
            ],
            [
                "IYJ",
                1.1274062660029818e-7,
                "0.000%"
            ],
            [
                "IYW",
                0.11506173687569335,
                "11.506%"
            ]
        ],
        "2016-01-31": [
            [
                "IBB",
                -0.15795032415421298,
                "-15.795%"
            ],
            [
                "IHE",
                -0.03561650459851761,
                "-3.562%"
            ],
            [
                "IVV",
                -3.453719001593711e-8,
                "-0.000%"
            ],
            [
                "IYC",
                0.00407690710234996,
                "0.408%"
            ],
            [
                "IYE",
                -0.0461325772879537,
                "-4.613%"
            ],
            [
                "IYF",
                -0.19721547151109614,
                "-19.722%"
            ],
            [
                "IYH",
                1.0297252173261136e-8,
                "0.000%"
            ],
            [
                "IYJ",
                0.5590081810898329,
                "55.901%"
            ],
            [
                "IYW",
                -5.900383288232142e-8,
                "-0.000%"
            ]
        ],
        "2016-02-29": [
            [
                "IBB",
                -0.17334007899401307,
                "-17.334%"
            ],
            [
                "IHE",
                -0.0030525666897426775,
                "-0.305%"
            ],
            [
                "IVV",
                0.3578852461246558,
                "35.789%"
            ],
            [
                "IYC",
                0.21749766042091495,
                "21.750%"
            ],
            [
                "IYE",
                0.10598792941982015,
                "10.599%"
            ],
            [
                "IYF",
                -0.14223518920164013,
                "-14.224%"
            ],
            [
                "IYH",
                -1.1988096189826629e-8,
                "-0.000%"
            ],
            [
                "IYJ",
                -0.0000017153793079871925,
                "-0.000%"
            ],
            [
                "IYW",
                -3.9826506994992615e-7,
                "-0.000%"
            ]
        ]
    }
})
#For testing
#if __name__ == "__main__":
#	app.run(debug=True, port=8080)

#For Production
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=8080)