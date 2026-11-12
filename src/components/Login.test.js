import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import Admin from './Admin';
import GeneralUser from './GeneralUser';
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({useNavigate: () => mockNavigate}));
beforeEach(() => {jest.clearAllMocks(); localStorage.clear(); global.fetch = jest.fn();});
test('unregistered Gmail displays user not found and does not navigate', async () => {
  fetch.mockResolvedValue({ok:false, json:async () => ({message:'NotFound'})});
  render(<GeneralUser/>);
  fireEvent.change(screen.getByLabelText('Gmail address'), {target:{value:'unknown@gmail.com'}});
  fireEvent.click(screen.getByRole('button', {name:'Login'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('User not found');
  expect(mockNavigate).not.toHaveBeenCalled();
  expect(fetch).toHaveBeenCalledWith('/api/generaluserlogin', expect.objectContaining({credentials:'include',body:JSON.stringify({gmail:'unknown@gmail.com'})}));
});
test('valid admin credentials navigate after the API succeeds', async () => {
  fetch.mockResolvedValue({ok:true, json:async () => ({message:'Success', username:'admin',usertype:'admin'})});
  render(<Admin/>);
  fireEvent.change(screen.getByLabelText('Username'), {target:{value:'admin'}});
  fireEvent.change(screen.getByLabelText('Password'), {target:{value:'admin'}});
  fireEvent.click(screen.getByRole('button', {name:'Login'}));
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/photo-portal'));
  expect(localStorage.getItem('usertype')).toBe('admin');
});
