import { BatchAnalysisResponse } from "@/services/abOptimizerService";

export const generateABAnalysisPDF = (analysisResult: BatchAnalysisResponse) => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    throw new Error("Please allow popups to export PDF");
  }

  const htmlContent = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>A/B Test Results</title>
        <style>
          body { font-family: system-ui, -apple-system, sans-serif; color: #111; line-height: 1.5; padding: 40px; max-width: 800px; margin: 0 auto; }
          h1 { color: #000; border-bottom: 2px solid #eee; padding-bottom: 10px; }
          h2 { color: #333; margin-top: 30px; }
          .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; background: #fff; page-break-inside: avoid; }
          .recommendation-card { background: #f0fdfa; border-color: #14b8a6; }
          .grid { display: flex; gap: 20px; }
          .col { flex: 1; }
          .img-preview { width: 100%; max-width: 250px; height: 200px; object-fit: cover; border-radius: 8px; border: 1px solid #eee; margin-bottom: 10px; }
          .score-box { background: #f8fafc; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 15px; text-align: center; }
          .score-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }
          .score-value { font-size: 32px; font-weight: bold; color: #0f766e; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
          th, td { padding: 8px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
          th { color: #64748b; font-weight: 600; }
          .good { color: #059669; }
          .bad { color: #dc2626; }
          .insight-box { margin-bottom: 15px; }
          .insight-title { font-weight: 600; margin-bottom: 4px; font-size: 14px; }
          p { font-size: 14px; color: #334155; }
          @media print {
            body { padding: 0; }
            .card { break-inside: avoid; }
          }
        </style>
      </head>
      <body>
        <h1>A/B Test Optimization Results</h1>
        <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
        <p><strong>Total Images Analyzed:</strong> ${analysisResult.total_images}</p>
        
        ${analysisResult.recommended_pair ? `
        <div class="card recommendation-card">
          <h2 style="margin-top:0; color: #0f766e;">🎯 Recommended A/B Test Pair</h2>
          <p><strong>Score Gap:</strong> ${analysisResult.score_gap?.toFixed(2)}</p>
          <p>${analysisResult.test_advice}</p>
        </div>
        ` : ''}

        <h2>Image Rankings</h2>
        ${analysisResult.images.map((img, idx) => `
          <div class="card">
            <h3 style="margin-top:0;">#${idx + 1}: ${img.filename}</h3>
            <div class="grid">
              <div class="col" style="flex: 0 0 250px;">
                ${img.image_url ? `<img src="${img.image_url}" class="img-preview" alt="Preview"/>` : ''}
                <div class="score-box">
                  <div class="score-label">Composite Score</div>
                  <div class="score-value">${img.scores.composite_score.toFixed(1)}<span style="font-size:18px; color:#94a3b8;">/10</span></div>
                </div>
              </div>
              <div class="col">
                <table>
                  <tr><th>Metric</th><th>Score</th></tr>
                  <tr><td>Restaurant Relevance</td><td>${img.scores.restaurant_relevance.toFixed(1)}/10</td></tr>
                  <tr><td>Viral Potential</td><td>${img.scores.viral_potential.toFixed(1)}/10</td></tr>
                  <tr><td>Aesthetic Quality</td><td>${img.scores.aesthetic_quality.toFixed(1)}/10</td></tr>
                </table>
                
                <div class="insight-box good">
                  <div class="insight-title">✓ Strengths</div>
                  <p style="margin:0;">${img.why_good}</p>
                </div>
                
                <div class="insight-box bad">
                  <div class="insight-title">⚠ Weaknesses</div>
                  <p style="margin:0;">${img.why_bad}</p>
                </div>
                
                <div class="insight-box" style="color: #0f766e;">
                  <div class="insight-title">💡 Recommendation</div>
                  <p style="margin:0;">${img.recommendation}</p>
                </div>
              </div>
            </div>
          </div>
        `).join('')}
      </body>
    </html>
  `;

  printWindow.document.write(htmlContent);
  printWindow.document.close();
  
  setTimeout(() => {
    printWindow.print();
  }, 500);
};
