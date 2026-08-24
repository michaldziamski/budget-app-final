import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StripePaymentModal from './StripePaymentModal';
import { paymentsAPI } from '../services/api';

jest.mock('../services/api', () => ({
  paymentsAPI: {
    getStripeConfig: jest.fn(),
    createPaymentForSavingsGoal: jest.fn(),
  },
}));

jest.mock('@stripe/stripe-js', () => ({
  loadStripe: jest.fn().mockResolvedValue({}),
}));

jest.mock('@stripe/react-stripe-js', () => {
  const original = jest.requireActual('@stripe/react-stripe-js');
  return {
    ...original,
    Elements: ({ children }) => <div data-testid="elements-wrapper">{children}</div>,
    CardElement: () => <div data-testid="card-element" />,
    useStripe: () => ({
      confirmCardPayment: jest.fn().mockResolvedValue({
        paymentIntent: { status: 'succeeded' },
      }),
    }),
    useElements: () => ({
      getElement: () => ({}),
      submit: jest.fn().mockResolvedValue({}),
    }),
  };
});

const goal = { id: 'goal-1', name: 'Test Goal' };

test('pokazuje loader gdy konfiguracja Stripe jeszcze się ładuje', () => {
  paymentsAPI.getStripeConfig.mockResolvedValueOnce({
    data: { publishable_key: 'pk_test_123' },
  });

  render(
    <StripePaymentModal
      open={true}
      onClose={jest.fn()}
      goal={goal}
      onSuccess={jest.fn()}
    />
  );

  expect(
    screen.getByText(/Ładowanie formularza płatności/i)
  ).toBeInTheDocument();
});

test.skip('po wpisaniu kwoty można przygotować płatność', async () => {
  paymentsAPI.getStripeConfig.mockResolvedValueOnce({
    data: { publishable_key: 'pk_test_123' },
  });

  paymentsAPI.createPaymentForSavingsGoal.mockResolvedValueOnce({
    data: { client_secret: 'cs_test_123' },
  });

  render(
    <StripePaymentModal
      open={true}
      onClose={jest.fn()}
      goal={goal}
      onSuccess={jest.fn()}
    />
  );

  // Poczekaj aż zniknie loader Stripe i pojawi się formularz
  await waitFor(() => {
    expect(
      screen.queryByText(/Ładowanie formularza płatności/i)
    ).not.toBeInTheDocument();
  });

  const amountInput = await screen.findByPlaceholderText('0.00');
  fireEvent.change(amountInput, { target: { value: '50' } });

  const prepareButton = await screen.findByText(/Przygotuj płatność/i);
  fireEvent.click(prepareButton);

  await waitFor(() => {
    expect(paymentsAPI.createPaymentForSavingsGoal).toHaveBeenCalledWith(
      goal.id,
      50
    );
  });
});


