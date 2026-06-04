import {describe, it, expect, vi} from 'vitest';
import {render, screen, act, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import {ToastProvider, useToast} from './toast-provider';

// Helper component that exposes the toast hook for testing
function TestConsumer() {
  const toast = useToast();
  return (
    <div>
      <span data-testid="toast-count">{toast.toasts.length}</span>
      <button onClick={() => toast.success('Success Title', 'Success message')}>success</button>
      <button onClick={() => toast.error('Error Title', 'Error message')}>error</button>
      <button onClick={() => toast.warning('Warning Title')}>warning</button>
      <button onClick={() => toast.info('Info Title')}>info</button>
    </div>
  );
}

describe('useToast', () => {
  it('should throw error when used outside ToastProvider', () => {
    // Suppress console.error for this test
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {
    });
    expect(() => render(<TestConsumer/>)).toThrow('useToast must be used within a ToastProvider');
    spy.mockRestore();
  });

  it('should provide empty toasts array initially', () => {
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );
    expect(screen.getByTestId('toast-count').textContent).toBe('0');
  });

  it('should add toast on success()', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );

    await user.click(screen.getByText('success'));
    expect(screen.getByTestId('toast-count').textContent).toBe('1');
    expect(screen.getByText('Success Title')).toBeInTheDocument();
    expect(screen.getByText('Success message')).toBeInTheDocument();
  });

  it('should add toast on error()', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );

    await user.click(screen.getByText('error'));
    expect(screen.getByTestId('toast-count').textContent).toBe('1');
    expect(screen.getByText('Error Title')).toBeInTheDocument();
  });

  it('should add toast on warning()', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );

    await user.click(screen.getByText('warning'));
    expect(screen.getByTestId('toast-count').textContent).toBe('1');
    expect(screen.getByText('Warning Title')).toBeInTheDocument();
  });

  it('should add toast on info()', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );

    await user.click(screen.getByText('info'));
    expect(screen.getByTestId('toast-count').textContent).toBe('1');
    expect(screen.getByText('Info Title')).toBeInTheDocument();
  });

  it('should limit to 5 toasts (max)', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );

    // Add 6 toasts
    for (let i = 0; i < 6; i++) {
      await user.click(screen.getByText('success'));
    }
    // Should be capped at 5 (the provider slices to keep max 5)
    expect(screen.getByTestId('toast-count').textContent).toBe('5');
  });

  it('should allow dismissing a toast', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestConsumer/>
      </ToastProvider>
    );

    await user.click(screen.getByText('success'));
    expect(screen.getByTestId('toast-count').textContent).toBe('1');

    // Click the close button on the toast (aria-label is "关闭")
    const closeButton = screen.getByRole('button', {name: '关闭'});
    await user.click(closeButton);

    // Toast removal has a 300ms animation delay
    await waitFor(() => {
      expect(screen.getByTestId('toast-count').textContent).toBe('0');
    });
  });
});
