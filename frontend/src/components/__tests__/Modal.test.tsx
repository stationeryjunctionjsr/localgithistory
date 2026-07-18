import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Modal from '../Modal';

describe('Modal Component', () => {
  it('renders the modal when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        <div>Content goes here</div>
      </Modal>
    );
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Content goes here')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <Modal isOpen={false} onClose={() => {}} title="Hidden">
        <div>Should not be visible</div>
      </Modal>
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} title="Close Test">
        <div>Close me</div>
      </Modal>
    );
    const closeBtn = screen.getByRole('button');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
