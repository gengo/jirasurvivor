/*global window, document, $, Raphael */

var survivor = survivor || {};

survivor.dashboard = (function () {
    'use strict';

    // ----------------------------------------
    // Charts

    // Parse an ISO-8601-formatted date string
    function parseDate(s) {
        return new Date(Date.parse(s));
    }

    // Extract data from each row in the <tbody> of `dataTable`. Each function
    // in `mappers` transforms values in a single column
    function extractData(dataTable, mappers) {
        return $.makeArray($(dataTable).find('tbody tr')).map(function (tr) {
            return mappers.map(function (mapper, idx) {
                return mapper($(tr).find('td:nth-child(' + (idx + 1) + ')').text());
            });
        });
    }

    // logical chart units
    var CHART_WIDTH = 1000,
        CHART_HEIGHT = 1000;

    // Create various chart elements, using `drawFn` to render the chart body
    function createChart(title, drawFn) {
        var $container = $('<div class="chart-container">');
        var $chart = $('<div class="chart">');

        $container.append('<label>' + title + '</label>');
        $container.append($chart);

        var chart = new Raphael($chart.get(0), '100%', '100%');
        chart.setViewBox(0, 0, CHART_WIDTH, CHART_HEIGHT);
        // This isn't supported natively in Raphael
        chart.canvas.setAttribute('preserveAspectRatio', 'none');

        drawFn(chart);

        return $container;
    }

    // Initialise bug rate chart
    // args: {
    //   dataTable: <datatable element>,
    //   colours: <array of column colours>,
    //   dateFormat: <h-axis date format>
    // }
    function initBugRateChart(args) {
        var $dataTable = $(args.dataTable);

        var data = extractData($dataTable, [parseDate, parseInt, parseInt]);
        var maxValue = Math.max.apply(null, data.map(function (row) {
            return Math.max(row[1], row[2]);
        }));
        // total cols = 2 cols per group + 1-col gap between each group
        var colWidth = CHART_WIDTH / (data.length * 3 - 1);

        var container = createChart($dataTable.attr('summary'), function (chart) {
            // var cols = data.map(function (row, rowIdx) {
            //     return {};
            // });
            // cols.forEach(function (col) {
            //     chart.rect();
            // });
            data.forEach(function (row, rowIdx) {
                row.slice(1).forEach(function (val, colIdx) {
                    var colHeight = val / maxValue * CHART_HEIGHT;
                    var hOffset = colWidth * (3 * rowIdx + colIdx);
                    var vOffset = CHART_HEIGHT - colHeight;
                    var col = chart.rect(hOffset,
                                         vOffset,
                                         colWidth,
                                         colHeight);
                    col.attr('fill', args.colours[colIdx]);
                    col.attr('stroke-width', 0);
                });
            });
        });

        $dataTable.replaceWith(container);
    }

    // Initialise open bug count chart
    // args: {
    //   containerId: <datatable element>,
    //   colours: { line: <line colour>, area: <area colour> },
    //   dateFormat: <h-axis date format>
    // }
    function initBugCountChart(args) {
        var $dataTable = $(args.dataTable);

        var data = extractData($dataTable, [parseDate, parseInt]);
        var maxValue = Math.max.apply(null, data.map(function (row) {
            return row[1];
        }));
        var hOffset = CHART_WIDTH / (data.length - 1);

        var strokeWidth = 10;

        var container = createChart($dataTable.attr('summary'), function (chart) {
            var points = data.map(function (row, idx) {
                var val = row[1];
                return { x: hOffset * idx,
                         y: CHART_HEIGHT - (val / maxValue) * CHART_HEIGHT };
            });

            // close the path, allowing for stroke width
            // XXX: this is cheating
            points[0].x -= strokeWidth;
            points[points.length - 1].x += strokeWidth;
            points.push({ x: CHART_WIDTH + strokeWidth, y: CHART_HEIGHT + strokeWidth });
            points.push({ x: -strokeWidth, y: CHART_HEIGHT + strokeWidth });

            // Is this really how paths are created in SVG? :(
            var pathStr =
                'M ' +
                points.map(function (p) { return p.x + ' ' + p.y; }).join(' L ') +
                ' z';

            var line = chart.path(pathStr);
            line.attr({
                'stroke': args.colours.line,
                'stroke-width': strokeWidth,
                'fill': args.colours.area
            });
        });

        $dataTable.replaceWith(container);
    }

    // ----------------------------------------
    // Initialisation

    $(function () {
        initBugRateChart({
            dataTable: $('#bug-rate-data'),
		    colours: ['#1CAD7E', '#0B4532']
		});

	    initBugCountChart({
            dataTable: $('#open-bug-data'),
		    colours: { line: '#9EC6A3', area: '#00815A' }
		});

        // Refresh every 10 minutes to get latest data
        window.setTimeout(function () { window.location.reload(); }, 1000 * 60 * 10);
    });
}());
