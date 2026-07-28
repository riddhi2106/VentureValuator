import { test, expect } from '@playwright/test';

test.setTimeout(120000); // 2 minutes

test('user can generate and download investment memo and pitch deck', async ({ page }) => {
  await page.goto('http://localhost:8501/');

  // Upload startup document
  await page
    .getByTestId('stFileUploaderDropzoneInput')
    .setInputFiles('Untitled document (4).pdf');

  // Generate outputs
  await page.getByTestId('stBaseButton-primary').click();

  // Verify outputs were generated
  await expect(
  page.getByRole('button', {
    name: 'Download memo.txt'
  })
    ).toBeVisible();

  await expect(
    page.getByRole('button', { name: 'Download pitch deck (.pptx)' })
  ).toBeVisible();

  // Download memo
  const memoDownloadPromise = page.waitForEvent('download');

  await page.getByRole('button', {
    name: 'Download memo.txt'
  }).click();

  const memoDownload = await memoDownloadPromise;

  expect(
    memoDownload.suggestedFilename()
  ).toContain('memo');

  // Download pitch deck
  const pptDownloadPromise = page.waitForEvent('download');

  await page.getByRole('button', {
    name: 'Download pitch deck (.pptx)'
  }).click();

  const pptDownload = await pptDownloadPromise;

  expect(
    pptDownload.suggestedFilename()
  ).toContain('.pptx');
});