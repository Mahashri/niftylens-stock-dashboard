# NiftyLens — Stock Performance Intelligence

A responsive, browser-first dashboard for exploring the stock performance workbook.

## Features
- Interactive ranking chart for each stock's highest available CAGR.
- Sector comparison using average recorded best CAGR.
- Summary metrics and automatically generated insights.
- Search, sector and data-quality filters; sortable stock table.
- Click any stock for a detailed profile and CAGR horizon chart.
- Export the currently filtered stocks to CSV.
- Import XLSX, XLS or CSV files directly in the browser.

## Use
1. Open the deployed GitHub Pages site.
2. Select **Choose file** and upload `Stocks_Tracker_All_Stocks_Corrected.xlsx`.
3. The dashboard prefers the **Corrected Stock Master** tab and otherwise attempts to detect a stock table in the workbook.
4. Search/filter, click a stock row, or export your filtered result.

## Privacy and data limitations
Workbook parsing happens in the browser. The workbook itself is not uploaded by this application. CMP, P/E, returns and CAGR values are historical/recorded workbook data, not live market quotes. Extreme historical returns, missing periods and unverified source values should be investigated before making decisions. This is an analysis tool, not investment advice.

## Deploy
A GitHub Actions workflow in `.github/workflows/pages.yml` deploys the static site to GitHub Pages on every push to `main`. In repository **Settings → Pages**, choose **GitHub Actions** as the build and deployment source if it is not already configured.
