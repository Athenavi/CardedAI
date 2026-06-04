import {describe, it, expect, vi} from 'vitest';
import {render, screen, act} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import {ConfirmProvider, useConfirm} from './confirm-provider';

// Helper component that calls confirm() on button click and shows result
function TestConsumer() {
  const confirm = useConfirm();
  const [result, setResult] = React.useState<string>('pending');

  const handleDanger = async () => {
    const r = await confirm({message: 'Delete this item?', variant: 'danger'});
    setResult(r ? 'confirmed' : 'cancelled');
  };

  const handleWarning = async () => {
    const r = await confirm({message: 'Are you sure?', variant: 'warning', title: 'Warning'});
    setResult(r ? 'confirmed' : 'cancelled');
  };

  const handleCustomText = async () => {
    const r = await confirm({
      message: 'Proceed?',
      confirmText: 'Yes, go ahead',
      cancelText: 'No, go back',
    });
    setResult(r ? 'confirmed' : 'cancelled');
  };

  return (
    <div>
      <span data-testid="result">{result}</span>
      <button onClick={handleDanger}>danger-confirm</button>
      <button onClick={handleWarning}>warning-confirm</button>
      <button onClick={handleCustomText}>custom-text</button>
    </div>
  );
}

describe('useConfirm', () => {
  it('should throw error when used outside ConfirmProvider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {
    });
    expect(() => render(<TestConsumer/>)).toThrow('useConfirm must be used within a ConfirmProvider');
    spy.mockRestore();
  });
});

describe('ConfirmProvider', () => {
  it('should render children without dialog by default', () => {
    render(
      <ConfirmProvider>
        <div>Child Content</div>
      </ConfirmProvider>
    );
    expect(screen.getByText('Child Content')).toBeInTheDocument();
  });

  it('should show danger dialog with default texts', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    await user.click(screen.getByText('danger-confirm'));

    // Dialog should appear
    expect(screen.getByText('Delete this item?')).toBeInTheDocument();
    expect(screen.getByText('确认操作')).toBeInTheDocument(); // default title
    expect(screen.getByText('取消')).toBeInTheDocument(); // default cancel text
    expect(screen.getByText('确认')).toBeInTheDocument(); // default confirm text
  });

  it('should resolve true when confirming', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    expect(screen.getByTestId('result').textContent).toBe('pending');

    await user.click(screen.getByText('danger-confirm'));
    await user.click(screen.getByText('确认'));

    expect(screen.getByTestId('result').textContent).toBe('confirmed');
  });

  it('should resolve false when cancelling', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    await user.click(screen.getByText('danger-confirm'));
    await user.click(screen.getByText('取消'));

    expect(screen.getByTestId('result').textContent).toBe('cancelled');
  });

  it('should resolve false when clicking backdrop', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    await user.click(screen.getByText('danger-confirm'));

    // Click the backdrop (the div with bg-black/50)
    const backdrop = document.querySelector('.bg-black\\/50');
    if (backdrop) {
      await user.click(backdrop);
    }

    expect(screen.getByTestId('result').textContent).toBe('cancelled');
  });

  it('should show custom title for warning variant', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    await user.click(screen.getByText('warning-confirm'));
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('should show custom button texts', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    await user.click(screen.getByText('custom-text'));
    expect(screen.getByText('Yes, go ahead')).toBeInTheDocument();
    expect(screen.getByText('No, go back')).toBeInTheDocument();
  });

  it('should close dialog after confirming', async () => {
    const user = userEvent.setup();
    render(
      <ConfirmProvider>
        <TestConsumer/>
      </ConfirmProvider>
    );

    await user.click(screen.getByText('danger-confirm'));
    expect(screen.getByText('Delete this item?')).toBeInTheDocument();

    await user.click(screen.getByText('确认'));
    expect(screen.queryByText('Delete this item?')).not.toBeInTheDocument();
  });
});
